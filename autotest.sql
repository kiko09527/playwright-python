/*
 Navicat Premium Data Transfer

 Source Server         : 001
 Source Server Type    : MySQL
 Source Server Version : 50720
 Source Host           : localhost:3306
 Source Schema         : autotest

 Target Server Type    : MySQL
 Target Server Version : 50720
 File Encoding         : 65001

 Date: 06/03/2025 14:59:44
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for http_seting_info
-- ----------------------------
DROP TABLE IF EXISTS `http_seting_info`;
CREATE TABLE `http_seting_info` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `script_name` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `url` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `assert_type` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `rule_type` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `assert_body_type` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `check_info` text CHARACTER SET utf8mb4,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for log_http
-- ----------------------------
DROP TABLE IF EXISTS `log_http`;
CREATE TABLE `log_http` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `script_name` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `unique_code` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `url` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `headers` longtext CHARACTER SET utf8mb4,
  `post_data` longtext CHARACTER SET utf8mb4,
  `method` text CHARACTER SET utf8mb4,
  `status` int(11) DEFAULT NULL,
  `body` longtext CHARACTER SET utf8mb4,
  `response_header` longtext CHARACTER SET utf8mb4,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `assert_status` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_nq` (`script_name`,`create_time`) USING BTREE,
  KEY `idx_nq2` (`unique_code`,`script_name`)
) ENGINE=InnoDB AUTO_INCREMENT=1296 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for script_execute_log
-- ----------------------------
DROP TABLE IF EXISTS `script_execute_log`;
CREATE TABLE `script_execute_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `script_name` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `post_data` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `mode` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `status` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `msg` text CHARACTER SET utf8mb4,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=145 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for script_info
-- ----------------------------
DROP TABLE IF EXISTS `script_info`;
CREATE TABLE `script_info` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `script_name` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `execute_mode` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `execute_time` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `need_api` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `filtered_apis` text CHARACTER SET utf8mb4,
  `delete_apis` text CHARACTER SET utf8mb4,
  `last_exec_status` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `send_email` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=latin1;

SET FOREIGN_KEY_CHECKS = 1;

DROP TABLE IF EXISTS `batch_execute_params`;
CREATE TABLE `batch_execute_params` (
                                        `id` bigint(20) NOT NULL AUTO_INCREMENT,
                                        `script_name` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT '脚本名称',
                                        `params_name` varchar(255) CHARACTER SET utf8mb4 DEFAULT NULL COMMENT '参数集名称',
                                        `params_data` longtext CHARACTER SET utf8mb4 COMMENT '参数数据JSON',
                                        `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
                                        `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                        PRIMARY KEY (`id`),
                                        KEY `idx_script_name` (`script_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批量执行参数表';
