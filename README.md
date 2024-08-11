# iptv-m3u-checker

## 功能

扫描指定目录下所有 m3u 文件收录新地址，检查收录地址的有效性，输出可用的 m3u 文件

## 环境

python+mysql

## 初始化数据库和配置

1.初始化 mysql 数据库

```sql
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
```

2.增加.env 文件

```code
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
#连接池名称比如my_pool
DB_POOL_NAME=
#连接池大小1-30
DB_POOL_SIZE=
```

## 运行

```bash
usage: iptv-m3u-checker.py [-h] [-i INPUT] [-c] [-f] [-o OUTPUT]

解析m3u文件，更新数据库，检查有效url，生成新的m3u文件。

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        解析文件夹下的所有.m3u文件，登记新记录。
  -c, --check           检查记录中的的url是否可用并记录。
  -f, --force           强制检查所有记录，默认只重新检查有效地址或新地址。配合-c使用。
  -o OUTPUT, --output OUTPUT
                        输出m3u文件。
```

## 其它

可以通过修改数据库整理分类和台标。
