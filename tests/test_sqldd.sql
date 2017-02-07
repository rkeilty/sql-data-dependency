SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS A;
DROP TABLE IF EXISTS D;
DROP TABLE IF EXISTS M;
DROP TABLE IF EXISTS P;
DROP TABLE IF EXISTS another_table;
DROP TABLE IF EXISTS one_more_table;

-- Create the tables
CREATE TABLE A (
  `a_id` INT NOT NULL,
  `d_fk_id` INT NULL,
  PRIMARY KEY (`a_id`)
);

CREATE TABLE D (
  `d_id` INT NOT NULL,
  `d_fk_id` INT NULL,
  `m_fk_id` INT NULL,
  PRIMARY KEY (`d_id`)
);

CREATE TABLE M (
  `m_id` INT NOT NULL,
  `d_fk_id` INT NULL,
  PRIMARY KEY (`m_id`)
);

CREATE TABLE P (
  `p_id` INT NOT NULL,
  PRIMARY KEY (`p_id`)
);

CREATE TABLE another_table (
  `another_table_id` INT NOT NULL,
  `p_fk_id` INT NULL,
  `one_more_table_id_fk_id` VARCHAR(30) NULL,
  PRIMARY KEY (`another_table_id`)
);

CREATE TABLE one_more_table (
  `one_more_table_id` VARCHAR(30) NOT NULL,
  `p_fk_id` INT NULL,
  PRIMARY KEY (`one_more_table_id`)
);

-- Put the foreign keys in place
ALTER TABLE A ADD CONSTRAINT a_d_fk_id FOREIGN KEY (d_fk_id) REFERENCES D (d_id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE D ADD CONSTRAINT d_d_fk_id FOREIGN KEY (d_fk_id) REFERENCES D (d_id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE D ADD CONSTRAINT d_m_fk_id FOREIGN KEY (m_fk_id) REFERENCES M (m_id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE M ADD CONSTRAINT m_d_fk_id FOREIGN KEY (d_fk_id) REFERENCES D (d_id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE another_table ADD CONSTRAINT another_table_p_fk_id FOREIGN KEY (p_fk_id) REFERENCES P (p_id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE another_table ADD CONSTRAINT another_table_one_more_table_id_fk_id FOREIGN KEY (one_more_table_id_fk_id) REFERENCES one_more_table (one_more_table_id) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE one_more_table ADD CONSTRAINT one_more_table_p_fk_id FOREIGN KEY (p_fk_id) REFERENCES P (p_id) ON UPDATE NO ACTION ON DELETE NO ACTION;

-- Put the sample data in place

INSERT INTO A (`a_id`, `d_fk_id`) VALUES (1, 22);
INSERT INTO D (`d_id`, `d_fk_id`, `m_fk_id`) VALUES (22, NULL, 3);
INSERT INTO M (`m_id`, `d_fk_id`) VALUES (3, NULL);

INSERT INTO A (`a_id`, `d_fk_id`) VALUES (53, 2);
INSERT INTO D (`d_id`, `d_fk_id`, `m_fk_id`) VALUES (2, 1, NULL);
INSERT INTO D (`d_id`, `d_fk_id`, `m_fk_id`) VALUES (1, NULL, 48);
INSERT INTO D (`d_id`, `d_fk_id`, `m_fk_id`) VALUES (20, NULL, NULL);
INSERT INTO M (`m_id`, `d_fk_id`) VALUES (48, 20);

INSERT INTO P (`p_id`) VALUES (800);
INSERT INTO P (`p_id`) VALUES (908);
INSERT INTO P (`p_id`) VALUES (1000);

INSERT INTO another_table (`another_table_id`, `p_fk_id`, `one_more_table_id_fk_id`) VALUES (1, NULL, NULL);
INSERT INTO another_table (`another_table_id`, `p_fk_id`, `one_more_table_id_fk_id`) VALUES (4, NULL, NULL);
INSERT INTO another_table (`another_table_id`, `p_fk_id`, `one_more_table_id_fk_id`) VALUES (10, NULL, 'string_pk_4444');

INSERT INTO one_more_table (`one_more_table_id`, `p_fk_id`) VALUES ('string_pk_1', 800);
INSERT INTO one_more_table (`one_more_table_id`, `p_fk_id`) VALUES ('string_pk_2', NULL);
INSERT INTO one_more_table (`one_more_table_id`, `p_fk_id`) VALUES ('string_pk_4444', 908);

SET FOREIGN_KEY_CHECKS=1;
