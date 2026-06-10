-- phpMyAdmin SQL Dump
-- version 4.9.0.1
-- https://www.phpmyadmin.net/
--
-- ホスト: localhost
-- 生成日時: 2020 年 4 月 15 日 17:45
-- サーバのバージョン： 5.5.60-MariaDB
-- PHP のバージョン: 5.6.40

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- データベース: `baogw`
--

-- --------------------------------------------------------

--
-- テーブルの構造 `gw_rules`
--

DROP TABLE IF EXISTS `gw_rules`;
CREATE TABLE `gw_rules` (
  `rule_id` int(10) UNSIGNED NOT NULL,
  `rule_status` tinyint(1) NOT NULL DEFAULT '0',
  `rule_set` int(11) DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `customer_name` varchar(128) CHARACTER SET utf8 NOT NULL,
  `hostname` varchar(256) CHARACTER SET utf8 NOT NULL,
  `ci_name` varchar(256) CHARACTER SET utf8 DEFAULT NULL,
  `action_no` int(11) NOT NULL DEFAULT '0',
  `op_comment` varchar(4000) CHARACTER SET utf8 DEFAULT NULL,
  `create_user` varchar(128) CHARACTER SET utf8 DEFAULT NULL,
  `update_user` varchar(128) CHARACTER SET utf8 DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- テーブルのデータのダンプ `gw_rules`
--

INSERT INTO `gw_rules` (`rule_id`, `rule_status`, `rule_set`, `start_time`, `end_time`, `customer_name`, `hostname`, `ci_name`, `action_no`, `op_comment`, `create_user`, `update_user`) VALUES
(1, 1, 1, '2020-03-01 09:00:00', '2021-03-31 09:00:00', '連携テスト', 'rule_10', '*', 10, '', 'Admin', 'Admin'),
(2, 1, 1, '2020-03-01 09:00:00', '2021-03-31 09:00:00', '連携テスト', 'rule_20', '*', 20, '', 'Admin', 'Admin'),
(3, 1, 1, '2020-03-01 09:00:00', '2021-03-31 09:00:00', '連携テスト', 'rule_30', '*', 30, '', 'Admin', 'Admin'),
(4, 1, 1, '2020-03-01 09:00:00', '2021-03-31 09:00:00', '検証02', 'rule_10', '*', 10, '', 'Admin', 'Admin'),
(5, 1, 1, '2020-03-01 09:00:00', '2021-03-31 09:00:00', '検証02', 'rule_20', '*', 20, '', 'Admin', 'Admin'),
(6, 1, 1, '2020-03-01 09:00:00', '2021-03-31 09:00:00', '検証02', 'rule_30', '*', 30, '', 'Admin', 'Admin');

--
-- ダンプしたテーブルのインデックス
--

--
-- テーブルのインデックス `gw_rules`
--
ALTER TABLE `gw_rules`
  ADD PRIMARY KEY (`rule_id`);

--
-- ダンプしたテーブルのAUTO_INCREMENT
--

--
-- テーブルのAUTO_INCREMENT `gw_rules`
--
ALTER TABLE `gw_rules`
  MODIFY `rule_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
