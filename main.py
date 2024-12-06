import asyncio
import aiohttp
from copy import deepcopy
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging
import sys
import os
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

API_VERSION = "5.199"

async def get_user_info(user_id, params, session):
    """Получает информацию о пользователе"""
    url = "https://api.vk.com/method/users.get"
    params = deepcopy(params)
    params["user_ids"] = user_id
    params["fields"] = "id,screen_name,first_name,last_name,sex,home_town,city"

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            user_info = data.get("response", [])[0]
            return user_info
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе {user_id}: {e}")
        return None

async def get_followers(user_id, params, session):
    """Получает фолловеров пользователя"""
    url = "https://api.vk.com/method/users.getFollowers"
    params = deepcopy(params)
    params["user_id"] = user_id
    params["fields"] = "id,screen_name,first_name,last_name,sex,home_town,city"

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            followers = data.get("response", {}).get("items", [])
            logger.info(f"Получены {len(followers)} фолловеров для пользователя {user_id}")
            return followers
    except Exception as e:
        logger.error(f"Ошибка при получении фолловеров для пользователя {user_id}: {e}")
        return []

async def get_subscriptions(user_id, params, session):
    """Получает подписки пользователя (на пользователей и группы)"""
    url = "https://api.vk.com/method/users.getSubscriptions"
    params = deepcopy(params)
    params["user_id"] = user_id
    params["extended"] = 1
    params["fields"] = "id,screen_name,name,first_name,last_name,type"

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            subscriptions = data.get("response", {}).get("items", [])
            logger.info(f"Получены {len(subscriptions)} подписок для пользователя {user_id}")
            return subscriptions
    except Exception as e:
        logger.error(f"Ошибка при получении подписок для пользователя {user_id}: {e}")
        return []

async def process_user(user_id, params, session, driver, current_depth, max_depth, processed_users_fetch, processed_users_save, processed_groups):
    """Рекурсивно получает данные пользователя и сохраняет в Neo4j"""
    if current_depth > max_depth or user_id in processed_users_fetch:
        return
    processed_users_fetch.add(user_id)

    user_info = await get_user_info(user_id, params, session)
    if not user_info:
        return

    save_user_to_neo4j(user_info, driver, processed_users_save)

    followers = await get_followers(user_id, params, session)

    for follower in followers:
        follower_id = int(follower['id'])
        save_user_to_neo4j(follower, driver, processed_users_save)
        save_follow_relationship(follower_id, user_id, driver)
        await asyncio.sleep(0.34)
        await process_user(follower_id, params, session, driver, current_depth + 1, max_depth, processed_users_fetch, processed_users_save, processed_groups)

    subscriptions = await get_subscriptions(user_id, params, session)

    for item in subscriptions:
        item_type = item.get('type')
        if item_type == 'profile':
            sub_user_id = int(item['id'])
            save_user_to_neo4j(item, driver, processed_users_save)
            save_subscribe_relationship_to_user(user_id, sub_user_id, driver)
            logger.debug(f"Связь Subscribe от пользователя {user_id} к пользователю {sub_user_id} создана")
        elif item_type in ('group', 'page'):
            group_id = int(item['id'])
            if group_id in processed_groups:
                continue
            processed_groups.add(group_id)
            save_group_to_neo4j(item, driver)
            save_subscribe_relationship_to_group(user_id, group_id, driver)
            logger.debug(f"Связь Subscribe от пользователя {user_id} к группе {group_id} создана")
        else:
            logger.warning(f"Неизвестный тип подписки {item_type} для элемента {item}")

        await asyncio.sleep(0.34)

def save_user_to_neo4j(user_info, driver, processed_users_save):
    """Сохраняет пользователя в Neo4j"""
    user_id = int(user_info['id'])
    if user_id in processed_users_save:
        return
    processed_users_save.add(user_id)
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (u:User {id: $id})
                SET u.screen_name = $screen_name,
                    u.name = $name,
                    u.sex = $sex,
                    u.home_town = $home_town,
                    u.city = $city
                """,
                id=user_id,
                screen_name=user_info.get('screen_name', ''),
                name=f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}",
                sex=user_info.get('sex', 0),
                home_town=user_info.get('home_town', ''),
                city=user_info.get('city', {}).get('title', '') if user_info.get('city') else ''
            )
        )
        logger.debug(f"Пользователь {user_id} сохранён в Neo4j")

def save_group_to_neo4j(group_info, driver):
    """Сохраняет группу в Neo4j"""
    group_id = int(group_info['id'])
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (g:Group {id: $id})
                SET g.name = $name,
                    g.screen_name = $screen_name
                """,
                id=group_id,
                name=group_info.get('name', ''),
                screen_name=group_info.get('screen_name', '')
            )
        )
        logger.debug(f"Группа {group_id} сохранена в Neo4j")

def save_follow_relationship(follower_id, user_id, driver):
    """Создаёт связь Follow"""
    follower_id = int(follower_id)
    user_id = int(user_id)
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (f:User {id: $follower_id})
                MERGE (u:User {id: $user_id})
                MERGE (f)-[:Follow]->(u)
                """,
                follower_id=follower_id,
                user_id=user_id
            )
        )
        logger.debug(f"Связь Follow от {follower_id} к {user_id} создана")

def save_subscribe_relationship_to_user(user_id, sub_user_id, driver):
    """Создаёт связь Subscribe от пользователя к пользователю"""
    user_id = int(user_id)
    sub_user_id = int(sub_user_id)
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (u1:User {id: $user_id})
                MERGE (u2:User {id: $sub_user_id})
                MERGE (u1)-[:Subscribe]->(u2)
                """,
                user_id=user_id,
                sub_user_id=sub_user_id
            )
        )
        logger.debug(f"Связь Subscribe от пользователя {user_id} к пользователю {sub_user_id} создана")

def save_subscribe_relationship_to_group(user_id, group_id, driver):
    """Создаёт связь Subscribe от пользователя к группе"""
    user_id = int(user_id)
    group_id = int(group_id)
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (u:User {id: $user_id})
                MERGE (g:Group {id: $group_id})
                MERGE (u)-[:Subscribe]->(g)
                """,
                user_id=user_id,
                group_id=group_id
            )
        )
        logger.debug(f"Связь Subscribe от пользователя {user_id} к группе {group_id} создана")

def run_queries(driver, queries):
    """Выполняет заданные запросы и выводит результаты"""
    with driver.session() as session:
        if 'total_users' in queries:
            total_users = session.run("MATCH (u:User) RETURN count(u) as total_users").single()["total_users"]
            logger.info(f"Всего пользователей: {total_users}")

        if 'total_groups' in queries:
            total_groups = session.run("MATCH (g:Group) RETURN count(g) as total_groups").single()["total_groups"]
            logger.info(f"Всего групп: {total_groups}")

        if 'top_users' in queries:
            top_users = session.run(
                """
                MATCH (u:User)<-[:Follow]-(f:User)
                RETURN u.id AS user_id, u.name AS name, count(f) AS followers_count
                ORDER BY followers_count DESC LIMIT 5
                """
            )
            logger.info("Топ 5 пользователей по количеству фолловеров:")
            for record in top_users:
                logger.info(f"Пользователь {record['name']} ({record['user_id']}) имеет {record['followers_count']} фолловеров")

        if 'top_groups' in queries:
            top_groups = session.run(
                """
                MATCH (g:Group)<-[:Subscribe]-(u:User)
                RETURN g.id AS group_id, g.name AS name, count(u) AS subscribers_count
                ORDER BY subscribers_count DESC LIMIT 5
                """
            )
            logger.info("Топ 5 самых популярных групп:")
            for record in top_groups:
                logger.info(f"Группа {record['name']} ({record['group_id']}) имеет {record['subscribers_count']} подписчиков")

        if 'mutual_followers' in queries:
            mutual_followers = session.run(
                """
                MATCH (u1:User)-[:Follow]->(u2:User), (u2)-[:Follow]->(u1)
                WHERE u1.id < u2.id  // Избегаем дубликатов
                RETURN u1.id AS user1_id, u1.name AS user1_name, u2.id AS user2_id, u2.name AS user2_name
                """
            )
            logger.info("Пользователи, которые фолловеры друг друга:")
            for record in mutual_followers:
                logger.info(
                    f"{record['user1_name']} ({record['user1_id']}) и {record['user2_name']} ({record['user2_id']})"
                )

async def main():
    # Загрузка параметров из переменных окружения
    TOKEN = os.getenv("TOKEN")
    DEFAULT_USER_ID = os.getenv("USER_ID")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    DEFAULT_MAX_DEPTH = int(os.getenv("MAX_DEPTH", 2))

    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="VK Data Collector and Neo4j Importer")
    parser.add_argument("--user_id", type=int, default=int(DEFAULT_USER_ID) if DEFAULT_USER_ID else None, help="ID пользователя для начала обхода")
    parser.add_argument("--max_depth", type=int, default=DEFAULT_MAX_DEPTH, help="Максимальная глубина рекурсии")
    parser.add_argument("--query", action='append', choices=['total_users', 'total_groups', 'top_users', 'top_groups', 'mutual_followers'], help="Запросы на выборку из базы данных")
    args = parser.parse_args()

    if not TOKEN or not args.user_id:
        logger.error("Необходимо указать TOKEN в файле .env и --user_id в аргументах командной строки или в файле .env")
        sys.exit(1)

    config = {
        "TOKEN": TOKEN,
        "USER_ID": args.user_id,
        "max_depth": args.max_depth,
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_password": NEO4J_PASSWORD,
    }

    logger.info("Запуск программы")

    params = {
        "v": API_VERSION,
        "access_token": config["TOKEN"],
    }

    driver = GraphDatabase.driver(config["neo4j_uri"], auth=(config["neo4j_user"], config["neo4j_password"]))

    processed_users_fetch = set()
    processed_users_save = set()
    processed_groups = set()

    async with aiohttp.ClientSession() as session:
        await process_user(
            config["USER_ID"],
            params,
            session,
            driver,
            current_depth=1,
            max_depth=config["max_depth"],
            processed_users_fetch=processed_users_fetch,
            processed_users_save=processed_users_save,
            processed_groups=processed_groups
        )

    if args.query:
        run_queries(driver, args.query)

    driver.close()
    logger.info("Программа завершена")

if __name__ == "__main__":
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
