-- Création des tables pour PicDash

CREATE TABLE profile (
  id CHAR(36) PRIMARY KEY,
  external_id VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  service VARCHAR(100) NOT NULL,
  updated_at DATETIME,
  posts_count INT DEFAULT 0,
  favorite VARCHAR(100)
);

CREATE TABLE profile_download (
  id CHAR(36) PRIMARY KEY,
  profile_id CHAR(36) NOT NULL,
  downloaded_at DATETIME NOT NULL,
  folder_path TEXT NOT NULL,
  FOREIGN KEY (profile_id) REFERENCES profile(id)
);
