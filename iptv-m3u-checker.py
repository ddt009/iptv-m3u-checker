import os
import time
import re
import requests
import threading
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv
import argparse

"""
# 建立数据表

CREATE TABLE `group` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `group` (`id`, `title`)
VALUES
	(1,'央视频道'),
	(2,'卫视频道'),
	(3,'地方频道'),
	(4,'其它频道'),
	(5,'域外频道'),
	(6,'未分类');

CREATE TABLE `tvg` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `group_id` int(11) DEFAULT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `logo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `url` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `tvg_id` int(11) DEFAULT NULL,
  `url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `passed_at` bigint(16) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=567 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

# 定义MySQL数据库配置文件 .env

DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
#连接池名称比如my_pool
DB_POOL_NAME=
#连接池大小1-30
DB_POOL_SIZE=

"""

load_dotenv()

# 定义MySQL数据库配置
db_config = {
    "pool_name": os.getenv("DB_POOL_NAME"),
    "pool_size": int(os.getenv("DB_POOL_SIZE")),
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT")),
}

# 创建MySQL连接池

pool = MySQLConnectionPool(
    pool_name=db_config["pool_name"],
    pool_size=db_config["pool_size"],
    host=db_config["host"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"],
    port=db_config["port"],
)


def get_group_id(group_title: str) -> int:
    conn = pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM `group` WHERE `title` = %s", (group_title,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            print(f"Inserting group: {group_title}")
            cursor.execute("INSERT INTO `group` (`title`) VALUES (%s)", (group_title,))
            conn.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            return result[0]
    finally:
        cursor.close()
        conn.close()


def get_tvg_id(tvg_name: str, group_id: int, tvg_log: str) -> int:
    conn = pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT `id` FROM `tvg` WHERE `name` = %s", (tvg_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            print(f"Inserting tvg: {tvg_name}")
            cursor.execute(
                "INSERT INTO `tvg` (`name`,`group_id`,`logo`) VALUES (%s,%s,%s )",
                (tvg_name, group_id, tvg_log),
            )
            conn.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            return result[0]
    finally:
        cursor.close()
        conn.close()


def update_url(url: str, tvg_id: int):
    conn = pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT `url` FROM `url` WHERE `url` = %s", (url,))
        result = cursor.fetchone()
        if not result:
            print(f"Inserting url: {url}")
            cursor.execute(
                "INSERT INTO `url` (`tvg_id`,`url`) VALUES (%s,%s)", (tvg_id, url)
            )
            conn.commit()
    finally:
        cursor.close()
        conn.close()


# 解析.m3u文件
def analyze_m3u_file(file_path):
    print(f"Analyzing file: {file_path}")

    # 打开.m3u文件
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    # 解析.m3u文件中的元素
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            try:
                # 使用正则表达式提取group-title、tvg-id和tvg-logo
                match = re.search(r'group-title="([^"]+)"', line)
                group_title = match.group(1) if match else None
                match = re.search(r'tvg-id="([^"]+)"', line)
                tvg_id = match.group(1) if match else None
                match = re.search(r'tvg-logo="([^"]+)"', line)
                tvg_logo = match.group(1) if match else None

                # 获取元素名称
                tv_name = (
                    line.split(",")[1] if line.index(",") < len(line) - 1 else None
                )

                if not tv_name and tvg_id:
                    tv_name = tvg_id

                # 获取URL
                url = lines[i + 1].strip() if i + 1 < len(lines) else None
                if url and not url.startswith("http"):
                    url = None

                group_id = 0  # 默认0为‘未分类’

                if tv_name and url:
                    if group_title:
                        group_id = get_group_id(group_title)  # 获取分组ID

                tvg_id = get_tvg_id(tv_name, group_id, tvg_logo)

                update_url(url, tvg_id)

            except IndexError:
                print(f"Invalid line format: {line}")


# 解析文件夹下的所有.m3u文件
def analyze_m3u_files_in_folder(folder_path):
    # 遍历文件夹下的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".m3u"):
                file_path = os.path.join(root, file)
                analyze_m3u_file(file_path)


def check_url(force=0):

    print("check_url")
    conn = pool.get_connection()
    cursor = conn.cursor()
    try:

        max_threads = db_config["pool_size"] - 1
        if force == 1:
            sql = "SELECT `id`,`url` FROM `url` "
        else:
            sql = "SELECT `id`,`url` FROM `url` where  `passed_at` is null or `passed_at`!=0"

        cursor.execute(sql)
        rows = cursor.fetchall()
        threads = []
        for row in rows:
            # 取得id和url值
            id = row[0]
            url = row[1]
            while threading.active_count() > max_threads:
                time.sleep(1)
            thread = threading.Thread(target=check_url_thread, args=(id, url))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        cursor.close()
        conn.close()


def check_url_thread(id, url):
    print(f"Checking URL: {id}:{url}")

    conn = pool.get_connection()
    cursor = conn.cursor()
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            cursor.execute(
                f"UPDATE `url` SET `passed_at` = {int(time.time())} WHERE id = {id}"
            )
            conn.commit()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while accessing URL: {url}")
        print(f"Error: {e}")
        cursor.execute(f"UPDATE `url` SET `passed_at` = 0 WHERE `id` = {id}")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def makem3u(output):
    print(f"输出有效url生成{output}...")
    conn = pool.get_connection()
    cursor = conn.cursor()
    try:

        sql = "select T.`name`,G.`title`,T.`logo`,U.`url` from `url` U left join tvg T on U.`tvg_id`=T.`id` left join `group` G on T.`group_id`=G.`id` where U.`passed_at`>0 order by T.`group_id`,T.`name`"
        cursor.execute(sql)
        rows = cursor.fetchall()
        with open(output, "w", encoding="utf-8") as f:
            f.write('#EXTM3U x-tvg-url="https://live.fanmingming.com/e.xml"\n')
            for row in rows:
                name = row[0]
                title = row[1]
                logo = row[2]
                url = row[3]
                f.write(
                    f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{title}",{name}\n {url}\n'
                )
        print("生成完成")
    finally:
        cursor.close()
        conn.close()


def main():

    parser = argparse.ArgumentParser(
        description="解析m3u文件，更新数据库，检查有效url，生成新的m3u文件。"
    )

    # 添加互斥组，使得 -c, -i, 和 -o 不能同时出现
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c", "--check", action="store_true", help="检查记录中的的url是否可用并记录."
    )
    group.add_argument(
        "-i", "--input", type=str, help="解析文件夹下的所有.m3u文件，登记新记录."
    )
    group.add_argument("-o", "--output", type=str, help="输出m3u文件.")

    # 添加 --force 选项，但只在与 --check 一起使用时才有效
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="强制检查所有记录，默认只重新检查有效地址或新地址.",
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 检查 -f 是否与 -c 一起使用
    if args.force and not args.check:
        parser.error("-f/--force can only be used with -c/--check.")

    # 检查是否有 -h 或 --help 选项，如果有则打印帮助信息并退出
    if len(vars(args)) > 0 and any(arg in vars(args) for arg in ["-h", "--help"]):
        parser.print_help()
        return

    # 根据提供的参数执行相应的操作
    if args.check:
        check_url(force=args.force)
    elif args.input:
        analyze_m3u_files_in_folder(args.input)
    elif args.output:
        makem3u(args.output)
    else:
        print("No action specified. Use -h or --help for more information.")


if __name__ == "__main__":
    main()
