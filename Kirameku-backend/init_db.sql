-- ============================================================================
-- Ynchen. ~ Blog — MySQL 8.0 建表脚本
-- 执行方式: mysql -u root -p kirameku < init_db.sql
-- 要求: MySQL 8.0+
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `kirameku`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `kirameku`;

-- ============================================
-- 1. user（用户/管理员）
-- ============================================
CREATE TABLE IF NOT EXISTS `user` (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)   NOT NULL UNIQUE,
    hashed_password VARCHAR(128)  NOT NULL,
    nickname        VARCHAR(50)   DEFAULT '',
    avatar          VARCHAR(500)  DEFAULT '',
    email           VARCHAR(100)  DEFAULT '',
    bio             VARCHAR(500)  DEFAULT '',
    is_admin        TINYINT(1)    DEFAULT 0,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. category（分类）
-- ============================================
CREATE TABLE IF NOT EXISTS `category` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(50)   NOT NULL UNIQUE,
    slug          VARCHAR(50)   NOT NULL UNIQUE,
    description   VARCHAR(200)  DEFAULT '',
    sort          INT           DEFAULT 0,
    post_count    INT           DEFAULT 0,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. tag（标签）
-- ============================================
CREATE TABLE IF NOT EXISTS `tag` (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(50)  NOT NULL UNIQUE,
    slug       VARCHAR(50)  NOT NULL UNIQUE,
    post_count INT          DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. post（文章）
-- ============================================
CREATE TABLE IF NOT EXISTS `post` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    slug          VARCHAR(200) NOT NULL UNIQUE,
    description   VARCHAR(500) DEFAULT '',
    content       MEDIUMTEXT,
    cover         VARCHAR(500) DEFAULT '',
    category_id   INT          DEFAULT NULL,
    status        VARCHAR(20)  DEFAULT 'draft',
    is_pinned     TINYINT(1)   DEFAULT 0,
    views         INT          DEFAULT 0,
    likes         INT          DEFAULT 0,
    word_count    INT          DEFAULT 0,
    reading_time  INT          DEFAULT 0,
    published_at  DATETIME     DEFAULT NULL,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_post_slug       (slug),
    INDEX idx_post_status     (status),
    INDEX idx_post_category   (category_id),

    CONSTRAINT fk_post_category
        FOREIGN KEY (category_id) REFERENCES `category`(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. post_tag（文章-标签 中间表）
-- ============================================
CREATE TABLE IF NOT EXISTS `post_tag` (
    post_id  INT NOT NULL,
    tag_id   INT NOT NULL,
    PRIMARY KEY (post_id, tag_id),

    CONSTRAINT fk_post_tag_post
        FOREIGN KEY (post_id) REFERENCES `post`(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_post_tag_tag
        FOREIGN KEY (tag_id) REFERENCES `tag`(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. github_user（GitHub 登录用户）
-- ============================================
CREATE TABLE IF NOT EXISTS `github_user` (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    github_id  INT          NOT NULL UNIQUE,
    login      VARCHAR(100) NOT NULL,
    avatar     VARCHAR(500) DEFAULT '',
    bio        VARCHAR(500) DEFAULT '',
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_github_user_github_id (github_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. comment（文章评论 — GitHub 登录）
-- ============================================
CREATE TABLE IF NOT EXISTS `comment` (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    post_id         INT          NOT NULL,
    parent_id       INT          DEFAULT NULL,
    github_user_id  INT          DEFAULT NULL,
    content         TEXT         NOT NULL,
    likes           INT          DEFAULT 0,
    ip              VARCHAR(45)  DEFAULT '',
    status          VARCHAR(20)  DEFAULT 'approved',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_comment_post        (post_id),
    INDEX idx_comment_status      (status),
    INDEX idx_comment_github_user (github_user_id),

    CONSTRAINT fk_comment_post
        FOREIGN KEY (post_id) REFERENCES `post`(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_comment_parent
        FOREIGN KEY (parent_id) REFERENCES `comment`(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_comment_github_user
        FOREIGN KEY (github_user_id) REFERENCES `github_user`(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 8. message（留言板/杂谈）
-- ============================================
CREATE TABLE IF NOT EXISTS `message` (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    github_user_id  INT          DEFAULT NULL,
    parent_id       INT          DEFAULT NULL,
    content         TEXT         NOT NULL,
    ip              VARCHAR(45)  DEFAULT '',
    status          VARCHAR(20)  DEFAULT 'approved',
    likes           INT          DEFAULT 0,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_message_status      (status),
    INDEX idx_message_parent      (parent_id),
    INDEX idx_message_github_user (github_user_id),

    CONSTRAINT fk_message_github_user
        FOREIGN KEY (github_user_id) REFERENCES `github_user`(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_message_parent
        FOREIGN KEY (parent_id) REFERENCES `message`(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 9. chatter（说说/微语）
-- ============================================
CREATE TABLE IF NOT EXISTS `chatter` (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    content         TEXT         NOT NULL,
    images          TEXT,
    mood            VARCHAR(20)  DEFAULT '',
    likes           INT          DEFAULT 0,
    comments_count  INT          DEFAULT 0,
    status          VARCHAR(20)  DEFAULT 'draft',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_chatter_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 10. chatter_comment（说说评论 — GitHub 登录）
-- ============================================
CREATE TABLE IF NOT EXISTS `chatter_comment` (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    chatter_id      INT          NOT NULL,
    parent_id       INT          DEFAULT NULL,
    github_user_id  INT          DEFAULT NULL,
    content         TEXT         NOT NULL,
    ip              VARCHAR(45)  DEFAULT '',
    likes           INT          DEFAULT 0,
    status          VARCHAR(20)  DEFAULT 'approved',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_chatter_comment_chatter     (chatter_id),
    INDEX idx_chatter_comment_status      (status),
    INDEX idx_chatter_comment_github_user (github_user_id),

    CONSTRAINT fk_chatter_comment_chatter
        FOREIGN KEY (chatter_id) REFERENCES `chatter`(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_chatter_comment_parent
        FOREIGN KEY (parent_id) REFERENCES `chatter_comment`(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_chatter_comment_github_user
        FOREIGN KEY (github_user_id) REFERENCES `github_user`(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 11. album（相册）
-- ============================================
CREATE TABLE IF NOT EXISTS `album` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(100) NOT NULL,
    description   VARCHAR(500) DEFAULT '',
    cover         VARCHAR(500) DEFAULT '',
    photo_count   INT          DEFAULT 0,
    sort          INT          DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 12. photo（照片）
-- ============================================
CREATE TABLE IF NOT EXISTS `photo` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    album_id      INT          NOT NULL,
    url           VARCHAR(500) NOT NULL,
    caption       VARCHAR(200) DEFAULT '',
    orientation   VARCHAR(20)  DEFAULT 'landscape',
    sort          INT          DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_photo_album (album_id),

    CONSTRAINT fk_photo_album
        FOREIGN KEY (album_id) REFERENCES `album`(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 13. project（项目展示）
-- ============================================
CREATE TABLE IF NOT EXISTS `project` (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    slug              VARCHAR(100) NOT NULL UNIQUE,
    description       VARCHAR(500) DEFAULT '',
    long_description  MEDIUMTEXT,
    cover_image       VARCHAR(500) DEFAULT '',
    tech_stack        TEXT,
    link_github       VARCHAR(300) DEFAULT '',
    link_gitee        VARCHAR(300) DEFAULT '',
    link_live         VARCHAR(300) DEFAULT '',
    link_docs         VARCHAR(300) DEFAULT '',
    status            VARCHAR(20)  DEFAULT 'developing',
    status_label      VARCHAR(20)  DEFAULT '',
    is_featured       TINYINT(1)   DEFAULT 0,
    sort              INT          DEFAULT 0,
    created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 14. friend_link（友情链接）
-- ============================================
CREATE TABLE IF NOT EXISTS `friend_link` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    url           VARCHAR(300) NOT NULL,
    avatar        VARCHAR(500) DEFAULT '',
    description   VARCHAR(300) DEFAULT '',
    sort          INT          DEFAULT 0,
    is_approved   TINYINT(1)   DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 15. bookmark_category（收藏夹分类）
-- ============================================
CREATE TABLE IF NOT EXISTS `bookmark_category` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(50)  NOT NULL,
    icon          VARCHAR(50)  DEFAULT '',
    description   VARCHAR(200) DEFAULT '',
    sort          INT          DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 16. bookmark_site（收藏站点）
-- ============================================
CREATE TABLE IF NOT EXISTS `bookmark_site` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    category_id   INT          NOT NULL,
    name          VARCHAR(100) NOT NULL,
    url           VARCHAR(300) NOT NULL,
    icon          VARCHAR(500) DEFAULT '',
    description   VARCHAR(300) DEFAULT '',
    platforms     TEXT,
    sort          INT          DEFAULT 0,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_bookmark_site_category (category_id),

    CONSTRAINT fk_bookmark_site_category
        FOREIGN KEY (category_id) REFERENCES `bookmark_category`(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 17. site_config（站点配置）
-- ============================================
CREATE TABLE IF NOT EXISTS `site_config` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    `key`         VARCHAR(100) NOT NULL UNIQUE,
    `value`       TEXT         DEFAULT NULL,
    description   VARCHAR(200) DEFAULT '',
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 18. visitor（访客记录）
-- ============================================
CREATE TABLE IF NOT EXISTS `visitor` (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ip            VARCHAR(45)  NOT NULL,
    `path`        VARCHAR(500) DEFAULT '',
    user_agent    TEXT,
    city          VARCHAR(100) DEFAULT '',
    region        VARCHAR(100) DEFAULT '',
    country       VARCHAR(100) DEFAULT '',
    district      VARCHAR(100) DEFAULT '',
    org           VARCHAR(200) DEFAULT '',
    asn           VARCHAR(50)  DEFAULT '',
    is_mobile     TINYINT(1)   DEFAULT 0,
    is_proxy      TINYINT(1)   DEFAULT 0,
    is_hosting    TINYINT(1)   DEFAULT 0,
    browser       VARCHAR(50)  DEFAULT '',
    os            VARCHAR(50)  DEFAULT '',
    device_type   VARCHAR(20)  DEFAULT '',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_visitor_ip      (ip),
    INDEX idx_visitor_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 初始数据：默认管理员（密码: admin123）
-- bcrypt hash of "admin123"
-- ============================================
INSERT IGNORE INTO `user` (username, hashed_password, nickname, is_admin)
VALUES (
    'admin',
    '$2b$12$ovrIaidgnmYaEQBYUZyZ8.IlJvbFeZZamGsYlHwU3MvPobMRPEAjC',
    '管理员',
    1
);

-- ============================================
-- 初始数据：默认站点配置
-- ============================================
INSERT IGNORE INTO `site_config` (`key`, `value`, description) VALUES
    ('site_title',              '"Ynchen. ~"',                         '站点标题'),
    ('site_description',        '"Ynchen. ~めく — 一个个人博客"',      '站点描述'),
    ('icp_number',              '""',                                  'ICP备案号'),
    ('icp_link',                '""',                                  'ICP备案链接'),
    ('cloud_music_playlist_id', '"12433389973"',                       '网易云歌单ID'),
    ('cloud_music_ids',         '[]',                                  '网易云歌曲ID列表（JSON数组，歌单为空时使用）');
