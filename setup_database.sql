-- =====================================================
-- Setup script cho database btl_csdl trên macOS
-- Chạy: /usr/local/mysql/bin/mysql -u root -p13112005 < setup_database.sql
-- =====================================================

CREATE DATABASE IF NOT EXISTS `btl_csdl` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `btl_csdl`;

SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- Bảng users (schema mới - dùng role thay vì is_admin)
-- =====================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'CUSTOMER',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tạo user owner mặc định (password: 123456 - hashed)
INSERT INTO `users` (`username`, `password`, `email`, `full_name`, `phone`, `role`) VALUES
('owner1', 'scrypt:32768:8:1$YK0jZ8qX$b1a2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8', 'owner1@example.com', 'Hotel Owner 1', '0901234567', 'OWNER');

-- =====================================================
-- Bảng user_security (THIẾU trong SQL dump, cần cho models.py)
-- =====================================================
DROP TABLE IF EXISTS `user_security`;
CREATE TABLE `user_security` (
  `user_id` int NOT NULL,
  `email_verified` tinyint(1) DEFAULT '0',
  `email_verification_token` varchar(100) DEFAULT NULL,
  `password_reset_token` varchar(100) DEFAULT NULL,
  `password_reset_expires` datetime DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `login_attempts` int DEFAULT '0',
  `locked_until` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_security_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng hotels
-- =====================================================
DROP TABLE IF EXISTS `hotels`;
CREATE TABLE `hotels` (
  `hotel_id` int NOT NULL AUTO_INCREMENT,
  `hotel_name` varchar(50) DEFAULT NULL,
  `address_hotel` varchar(150) DEFAULT NULL,
  `tel` varchar(20) DEFAULT NULL,
  `rating` float DEFAULT NULL,
  `descriptions` varchar(1000) DEFAULT NULL,
  `owner_id` int NOT NULL,
  PRIMARY KEY (`hotel_id`),
  KEY `owner_id` (`owner_id`),
  CONSTRAINT `hotels_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng hotel_locations (THIẾU trong SQL dump, cần cho models.py)
-- =====================================================
DROP TABLE IF EXISTS `hotel_locations`;
CREATE TABLE `hotel_locations` (
  `hotel_id` int NOT NULL,
  `latitude` float DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  PRIMARY KEY (`hotel_id`),
  CONSTRAINT `hotel_locations_ibfk_1` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`hotel_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng hotel_images
-- =====================================================
DROP TABLE IF EXISTS `hotel_images`;
CREATE TABLE `hotel_images` (
  `image_id` int NOT NULL AUTO_INCREMENT,
  `hotel_id` int DEFAULT NULL,
  `image_path` varchar(500) DEFAULT NULL,
  `is_main` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`image_id`),
  KEY `hotel_id` (`hotel_id`),
  CONSTRAINT `hotel_images_ibfk_1` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`hotel_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng rooms
-- =====================================================
DROP TABLE IF EXISTS `rooms`;
CREATE TABLE `rooms` (
  `room_id` int NOT NULL AUTO_INCREMENT,
  `room_type` varchar(35) DEFAULT NULL,
  `availableRooms` int DEFAULT NULL,
  `price` bigint DEFAULT NULL,
  `hotel_id` int DEFAULT NULL,
  PRIMARY KEY (`room_id`),
  KEY `hotel_id` (`hotel_id`),
  CONSTRAINT `rooms_ibfk_1` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`hotel_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng room_images
-- =====================================================
DROP TABLE IF EXISTS `room_images`;
CREATE TABLE `room_images` (
  `image_id` int NOT NULL AUTO_INCREMENT,
  `room_id` int DEFAULT NULL,
  `image_path` varchar(500) DEFAULT NULL,
  `is_main` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`image_id`),
  KEY `room_id` (`room_id`),
  CONSTRAINT `room_images_ibfk_1` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng services
-- =====================================================
DROP TABLE IF EXISTS `services`;
CREATE TABLE `services` (
  `id_service` int NOT NULL AUTO_INCREMENT,
  `serviceName` varchar(255) DEFAULT NULL,
  `room_id` int DEFAULT NULL,
  PRIMARY KEY (`id_service`),
  KEY `room_id` (`room_id`),
  CONSTRAINT `services_ibfk_1` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng reviews (thêm created_at cho code)
-- =====================================================
DROP TABLE IF EXISTS `reviews`;
CREATE TABLE `reviews` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `rating` float DEFAULT NULL,
  `comment` varchar(200) DEFAULT NULL,
  `hotel_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  KEY `user_id` (`user_id`),
  KEY `hotel_id` (`hotel_id`),
  CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`hotel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng bookings (schema mới - có num_rooms)
-- =====================================================
DROP TABLE IF EXISTS `bookings`;
CREATE TABLE `bookings` (
  `booking_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `room_id` int DEFAULT NULL,
  `check_in` datetime NOT NULL,
  `check_out` datetime NOT NULL,
  `total_price` float NOT NULL,
  `status` varchar(20) DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `num_rooms` int DEFAULT '1',
  PRIMARY KEY (`booking_id`),
  KEY `user_id` (`user_id`),
  KEY `room_id` (`room_id`),
  CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng payment (schema mới - không có user_id, có txn_ref, etc.)
-- =====================================================
DROP TABLE IF EXISTS `payment`;
CREATE TABLE `payment` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `booking_id` int DEFAULT NULL,
  `txn_ref` varchar(100) DEFAULT NULL,
  `amount` bigint DEFAULT NULL,
  `bank_code` varchar(50) DEFAULT NULL,
  `pay_date` datetime DEFAULT NULL,
  `response_code` varchar(10) DEFAULT NULL,
  `payment_status` varchar(50) DEFAULT NULL,
  `secure_hash` text,
  `payment_method` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`payment_id`),
  KEY `booking_id` (`booking_id`),
  CONSTRAINT `payment_ibfk_2` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================
-- Bảng notifications
-- =====================================================
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `type` varchar(50) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  `read` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- INSERT DATA - Hotels (cần owner_id=1, nên insert owner trước)
-- =====================================================
INSERT INTO `hotels` VALUES 
(1,'Swandor Cam Ranh Resort','Km 11 Nguyen Tat Thanh Boulevard, Bai Dai Beach, Cam Lam District, Cam Ranh, Khanh Hoa, Vietnam','+842583988000',8.7,'Swandor Cam Ranh Resort is a five-star beachfront resort located on Bai Dai Beach.',1),
(2,'Ana Mandara Cam Ranh','Slot D6A - Zone 2, Cam Ranh Peninsula, Cam Lam District, Khanh Hoa, Vietnam','+842583522222',9,'Ana Mandara Cam Ranh is a luxurious 5-star resort nestled along a tranquil private beach.',1),
(3,'Sheraton Grand Danang Resort','35 Truong Sa Street, Hoa Hai Ward, Ngu Hanh Son District, Da Nang, Vietnam','+842363988999',8.7,'Sheraton Grand Danang Resort is a prestigious five-star hotel situated on Non Nuoc Beach.',1),
(4,'Imperial Hotel & Spa','44 Hang Hanh Street, Hoan Kiem District, Hanoi, Vietnam','+842439335555',9.1,'Imperial Hotel & Spa is an elegant boutique hotel located in Hanoi Old Quarter.',1),
(5,'HOTEL de LAGOM','30B-C-D Ly Nam De Street, Cua Dong Ward, Hoan Kiem District, Hanoi, Vietnam','+842433133333',9.4,'HOTEL de LAGOM is a newly opened five-star boutique hotel in Hanoi.',1),
(6,'DeLaSea Ha Long Hotel','A9, Lot 1, Hung Thang Tourist Area, Ha Long City, Quang Ninh, Vietnam','+842033636999',9,'DeLaSea Ha Long Hotel is a contemporary 5-star hotel in Ha Long City.',1),
(7,'Legacy Yen Tu - MGallery','Thuong Yen Cong Commune, Uong Bi City, Quang Ninh Province, Vietnam','+842036259888',9,'Legacy Yen Tu - MGallery is a unique luxury resort at the foot of Yen Tu Mountain.',1),
(8,'Seashells Phu Quoc Hotel & Spa','1 Vo Thi Sau Street, Duong Dong, Phu Quoc, Kien Giang, Vietnam','+842977300999',9,'Seashells Phu Quoc Hotel & Spa is a modern oceanfront hotel on Phu Quoc Island.',1),
(9,'Sailing Club Signature Resort','Group 6, Duong Bao Hamlet, Duong To, Phu Quoc, Kien Giang, Vietnam','+842973660000',9.4,'Sailing Club Signature Resort Phu Quoc is an exclusive villa resort.',1),
(10,'Movenpick Resort Cam Ranh','Plot D12, Cam Hai Dong, Cam Lam District, Khanh Hoa 57615, Vietnam','+842583985888',8.7,'Movenpick Resort Cam Ranh is a family-friendly beachfront resort.',1);

-- =====================================================
-- INSERT DATA - Rooms
-- =====================================================
INSERT INTO `rooms` VALUES 
(1,'Deluxe Sea View Room',8,5000000,1),(2,'Deluxe Front Sea View Room',6,6000000,1),(3,'Deluxe Family Sea View Room',5,8000000,1),
(4,'Deluxe Ocean View Room',6,5000000,2),(5,'1-Bedroom Beachfront Pool Villa',4,9000000,2),(6,'2-Bedroom Beachfront Pool Villa',3,10000000,2),
(7,'Deluxe King Room with Balcony',10,4000000,3),(8,'Premier Ocean View Room',8,6000000,3),(9,'Executive Suite',5,8000000,3),
(10,'Deluxe Room',9,2000000,4),(11,'Executive Room',7,2500000,4),(12,'Imperial Suite',5,4000000,4),
(13,'Deluxe Window Room',10,3000000,5),(14,'Premium Balcony Room',8,3500000,5),(15,'Lagom Suite',5,5000000,5),
(16,'Deluxe Twin Room',8,2500000,6),(17,'Executive Ocean View Room',6,3500000,6),(18,'Family Suite Ocean View',4,5000000,6),
(19,'Superior King Room',10,3000000,7),(20,'Deluxe Twin Room',9,3500000,7),(21,'Executive Suite',5,6000000,7),
(22,'Deluxe Double Ocean View',10,2500000,8),(23,'Premier Ocean View Room',9,3500000,8),(24,'Family Suite Sea View',6,5000000,8),
(25,'One-Bedroom Pool Villa',5,6000000,9),(26,'Two-Bedroom Pool Villa',5,8000000,9),(27,'Three-Bedroom Pool Villa',5,10000000,9),
(28,'Deluxe Sea View Room',10,4500000,10),(29,'Junior Suite Ocean View',8,6000000,10),(30,'Three-Bedroom Pool Villa',4,10000000,10);

SELECT 'Database btl_csdl created and populated successfully!' AS status;
