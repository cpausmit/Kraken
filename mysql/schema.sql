-- Kraken production database 'Bambu' -- schema of record.
--
-- Read off the live server on 2026-09-22 by ds.sh.
-- See README.md in this directory for what the tables mean and how to connect.
--
-- Regenerate (from t3desk000.mit.edu as cmsprod):
--
--     ./ds.sh > schema.sql
--
-- AUTO_INCREMENT counters are stripped: they are state, not schema.

CREATE DATABASE IF NOT EXISTS Bambu;
USE Bambu;
-- Skipped as scratch (matching _backup_|_test$|_test_): Blocks_backup_20260922 Lfns_backup_20260922 

CREATE TABLE `Datasets` (
  `DatasetId` mediumint(9) NOT NULL AUTO_INCREMENT,
  `DatasetProcess` varchar(333) NOT NULL,
  `DatasetSetup` varchar(333) NOT NULL,
  `DatasetTier` varchar(333) NOT NULL,
  `DatasetDbsInstance` varchar(60) DEFAULT NULL,
  `DatasetSizeGb` double NOT NULL DEFAULT -1,
  `DatasetNFiles` mediumint(9) NOT NULL DEFAULT -1,
  PRIMARY KEY (`DatasetId`),
  UNIQUE KEY `id` (`DatasetProcess`,`DatasetSetup`,`DatasetTier`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `Blocks` (
  `BlockId` int(11) NOT NULL AUTO_INCREMENT,
  `DatasetId` mediumint(9) NOT NULL,
  `BlockName` char(36) NOT NULL,
  PRIMARY KEY (`BlockId`),
  KEY `DatasetId` (`DatasetId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `Lfns` (
  `DatasetId` mediumint(9) NOT NULL,
  `BlockId` int(11) NOT NULL,
  `FileName` varchar(255) DEFAULT NULL,
  `PathName` text DEFAULT NULL,
  `NEvents` mediumint(9) NOT NULL DEFAULT -1,
  UNIQUE KEY `LfnId` (`DatasetId`,`BlockId`,`FileName`),
  KEY `DatasetId` (`DatasetId`),
  KEY `BlockId` (`BlockId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `Requests` (
  `RequestId` mediumint(9) NOT NULL AUTO_INCREMENT,
  `DatasetId` mediumint(9) NOT NULL,
  `RequestConfig` varchar(333) NOT NULL,
  `RequestVersion` varchar(333) NOT NULL,
  `RequestPy` varchar(33) NOT NULL,
  `RequestNFilesDone` mediumint(9) NOT NULL DEFAULT -1,
  PRIMARY KEY (`RequestId`),
  UNIQUE KEY `id` (`DatasetId`,`RequestConfig`,`RequestVersion`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `Files` (
  `RequestId` mediumint(9) NOT NULL,
  `FileName` varchar(255) DEFAULT NULL,
  `NEvents` mediumint(9) NOT NULL DEFAULT -1,
  `SizeBytes` bigint(20) DEFAULT 0,
  UNIQUE KEY `id` (`RequestId`,`FileName`),
  KEY `RequestId` (`RequestId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
