CREATE TABLE IF NOT EXISTS `mentions` (
  `user` varchar(20) NOT NULL,
  `mentions_comment` int(11) NOT NULL,
  `mentions_selftext` int(11) NOT NULL,
  `mentions_title` int(11) NOT NULL,
  UNIQUE KEY `user` (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
