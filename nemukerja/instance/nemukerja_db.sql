SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `nemukerja_db`
--

--
-- Table structure for `users` - MODIFIED FOR SECURE PASSWORDS
--
CREATE TABLE `users` (
  `id_user` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL, -- CHANGED from 'password'
  `role` enum('applicant','company','admin') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `applicants` (
  `id_applicant` int(11) NOT NULL,
  `id_user` int(11) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `cv_path` varchar(255) DEFAULT NULL,
  `skills` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `companies` (
  `id_company` int(11) NOT NULL,
  `id_user` int(11) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `contact_email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Table structure for `job_listings` - MODIFIED TO INCLUDE SLOTS and IS_OPEN
--
CREATE TABLE `job_listings` (
  `id_job` int(11) NOT NULL,
  `id_company` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `qualifications` text NOT NULL,
  `location` varchar(255) DEFAULT NULL,
  `slots` int(11) NOT NULL DEFAULT 1, -- ADDED
  `is_open` tinyint(1) NOT NULL DEFAULT 1, -- ADDED
  `posted_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `applications` (
  `id_application` int(11) NOT NULL,
  `id_applicant` int(11) NOT NULL,
  `id_job` int(11) NOT NULL,
  `status` enum('Pending','Diterima','Ditolak') NOT NULL DEFAULT 'Pending',
  `notes` text DEFAULT NULL,
  `applied_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users` with HASHED PASSWORDS
--
INSERT INTO `users` (`id_user`, `email`, `password_hash`, `role`) VALUES
(1, 'user@example.com', '$2b$12$0gU22A0F.0s4sQ8c.X5fIuLwT4G/cHnQv2Y8g.WO9ajp3A5vF3hHS', 'applicant'), -- Password is 'password'
(2, 'admin@nemukerja.com', '$2b$12$z2f.o2z7w.G2y.n0E1x.aO1E5N.U3z7W.z2b.o3g.K4s.N1E.s2z7', 'admin');     -- Password is 'adminpassword'

INSERT INTO `applicants` (`id_applicant`, `id_user`, `full_name`) VALUES (1, 1, 'Test User');

--
-- Indexes and Constraints
--
ALTER TABLE `users` ADD PRIMARY KEY (`id_user`), ADD UNIQUE KEY `email_unique` (`email`);
ALTER TABLE `applicants` ADD PRIMARY KEY (`id_applicant`), ADD KEY `idx_id_user` (`id_user`);
ALTER TABLE `companies` ADD PRIMARY KEY (`id_company`), ADD KEY `idx_id_user` (`id_user`);
ALTER TABLE `job_listings` ADD PRIMARY KEY (`id_job`), ADD KEY `idx_id_company` (`id_company`);
ALTER TABLE `applications` ADD PRIMARY KEY (`id_application`), ADD KEY `idx_id_applicant` (`id_applicant`), ADD KEY `idx_id_job` (`id_job`);

ALTER TABLE `users` MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
ALTER TABLE `applicants` MODIFY `id_applicant` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
ALTER TABLE `companies` MODIFY `id_company` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `job_listings` MODIFY `id_job` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `applications` MODIFY `id_application` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `applicants` ADD CONSTRAINT `applicants_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE;
ALTER TABLE `companies` ADD CONSTRAINT `companies_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE;
ALTER TABLE `job_listings` ADD CONSTRAINT `job_listings_ibfk_1` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE CASCADE;
ALTER TABLE `applications` ADD CONSTRAINT `applications_ibfk_1` FOREIGN KEY (`id_applicant`) REFERENCES `applicants` (`id_applicant`) ON DELETE CASCADE, ADD CONSTRAINT `applications_ibfk_2` FOREIGN KEY (`id_job`) REFERENCES `job_listings` (`id_job`) ON DELETE CASCADE;
COMMIT;