-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 20 Okt 2025 pada 04.51
-- Versi server: 10.4.28-MariaDB
-- Versi PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `nemukerja_db`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `applicants`
--

CREATE TABLE `applicants` (
  `id_applicant` int(11) NOT NULL,
  `id_user` int(11) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `cv_path` varchar(255) DEFAULT NULL,
  `skills` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `applicants`
--

INSERT INTO `applicants` (`id_applicant`, `id_user`, `full_name`, `cv_path`, `skills`, `created_at`, `updated_at`) VALUES
(3, 6, 'Kayla', NULL, NULL, '2025-10-12 14:57:14', '2025-10-12 14:57:14'),
(4, 7, 'Putri', NULL, NULL, '2025-10-15 04:35:31', '2025-10-15 04:35:31');

-- --------------------------------------------------------

--
-- Struktur dari tabel `applications`
--

CREATE TABLE `applications` (
  `id_application` int(11) NOT NULL,
  `id_applicant` int(11) NOT NULL,
  `id_job` int(11) NOT NULL,
  `status` enum('Pending','Diterima','Ditolak') NOT NULL DEFAULT 'Pending',
  `notes` text DEFAULT NULL,
  `applied_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `applications`
--

INSERT INTO `applications` (`id_application`, `id_applicant`, `id_job`, `status`, `notes`, `applied_at`, `updated_at`) VALUES
(2, 3, 4, 'Diterima', 'Lorem ipsum dolor sit amet consectetur, adipisicing elit. Enim dolorum, consequuntur ea molestias ducimus error nobis est, ullam illo nihil sunt aperiam libero totam qui placeat maxime labore saepe architecto quam esse illum autem quasi. Qui tempore aperiam dicta voluptates natus fuga. Possimus ab inventore molestiae consequatur facilis nihil voluptate quod, eveniet unde. Culpa eaque vel deleniti facilis magnam quis voluptate dolore, quae facere ipsa veniam velit ut officiis in error magni dignissimos necessitatibus eos impedit delectus. Possimus maxime dicta minima, dolores, at quas vel impedit nisi rem a quia, placeat totam dolorem ratione dolore aperiam perspiciatis. Aliquid, eius sequi!', '2025-10-12 16:21:43', '2025-10-12 16:23:42'),
(3, 3, 5, 'Ditolak', 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Nesciunt nulla molestiae aliquam repellat laborum, quibusdam sit qui tempora necessitatibus. Porro, laudantium quis consequatur dicta sunt earum, maxime nihil voluptate iure odit laboriosam cumque sapiente, aliquid dignissimos delectus necessitatibus molestiae voluptas. Hic accusantium voluptates et maxime eveniet veritatis fuga, corrupti, minima harum laboriosam quas eaque ratione vel dolores facilis aliquam recusandae nulla dicta at id architecto impedit incidunt. Cupiditate nobis sit, optio tempore ullam ut ducimus cumque repellendus aliquid. Unde hic dolores voluptatem illo reiciendis perspiciatis, doloremque facere dolor in maiores dicta doloribus exercitationem repellat tenetur recusandae cupiditate fugiat sunt sit?', '2025-10-13 01:40:26', '2025-10-13 01:41:01'),
(4, 4, 6, 'Diterima', 'nvewinvsoiadbvasndvuaiwervndsuvnsuidebgowiebgoqubgajdsbvuwebvuenuvweugnweunguprbgwrubsunvusebgweubgwubgb', '2025-10-15 04:36:04', '2025-10-15 04:36:45');

-- --------------------------------------------------------

--
-- Struktur dari tabel `companies`
--

CREATE TABLE `companies` (
  `id_company` int(11) NOT NULL,
  `id_user` int(11) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `contact_email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `companies`
--

INSERT INTO `companies` (`id_company`, `id_user`, `company_name`, `description`, `contact_email`, `phone`, `created_at`, `updated_at`) VALUES
(2, 5, 'Zhim Group', 'We are Zhim Group the one who control the world!', 'hafidzazhim@gmail.com', '081234567890', '2025-10-12 14:51:27', '2025-10-12 14:51:27');

-- --------------------------------------------------------

--
-- Struktur dari tabel `job_listings`
--

CREATE TABLE `job_listings` (
  `id_job` int(11) NOT NULL,
  `id_company` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `qualifications` text NOT NULL,
  `location` varchar(255) DEFAULT NULL,
  `posted_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `slots` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `job_listings`
--

INSERT INTO `job_listings` (`id_job`, `id_company`, `title`, `description`, `qualifications`, `location`, `posted_at`, `updated_at`, `slots`) VALUES
(4, 2, 'Security', 'Jago gebukin maling.', 'Minimal pendidikan SMA/SMK/Sederajat.', 'Batam', '2025-10-12 16:20:36', '2025-10-12 16:20:36', 2),
(5, 2, 'Agen Pemasaran', 'Jago hipnotis orang supaya mau beli produk kita ya.', 'S2, minimal pengalaman kerja 500 abad', 'Tanjungpinang', '2025-10-13 01:38:30', '2025-10-13 01:38:30', 1),
(6, 2, 'Office Boy', 'asnfouebgauisebviusabevisaundcinucnuiesnfvuiwenuiewnf', 'nuenfuiwenuiwenfewfwegwegwegfegewgw', 'Surabaya', '2025-10-15 04:28:42', '2025-10-15 04:28:42', 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `id_user` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('applicant','company') NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`id_user`, `email`, `password`, `role`, `created_at`, `updated_at`) VALUES
(5, 'hafidzazhim@gmail.com', '$2b$12$2avum7UC5GwNG5pGQQOaNOiECUoR784wHTa7tUFR/HY2dbF9s/oE6', 'company', '2025-10-12 14:51:27', '2025-10-12 14:51:27'),
(6, 'kayla@gmail.com', '$2b$12$5Z5kH0sArZygmW0GT34ZL./eQVkj/hiJjJ1L0Njcu9lCPnzDZhb7q', 'applicant', '2025-10-12 14:57:14', '2025-10-12 14:57:14'),
(7, 'zainaja123@gmail.com', '$2b$12$FvbcCDCrT//2.fTZadn7/Oo4/UzPxwDSmUbFvRiEmtqTw4WjuT70i', 'applicant', '2025-10-15 04:35:31', '2025-10-15 04:35:31');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indeks untuk tabel `applicants`
--
ALTER TABLE `applicants`
  ADD PRIMARY KEY (`id_applicant`),
  ADD KEY `idx_id_user` (`id_user`);

--
-- Indeks untuk tabel `applications`
--
ALTER TABLE `applications`
  ADD PRIMARY KEY (`id_application`),
  ADD KEY `idx_id_applicant` (`id_applicant`),
  ADD KEY `idx_id_job` (`id_job`);

--
-- Indeks untuk tabel `companies`
--
ALTER TABLE `companies`
  ADD PRIMARY KEY (`id_company`),
  ADD KEY `idx_id_user` (`id_user`);

--
-- Indeks untuk tabel `job_listings`
--
ALTER TABLE `job_listings`
  ADD PRIMARY KEY (`id_job`),
  ADD KEY `idx_id_company` (`id_company`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`),
  ADD UNIQUE KEY `email_unique` (`email`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `applicants`
--
ALTER TABLE `applicants`
  MODIFY `id_applicant` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT untuk tabel `applications`
--
ALTER TABLE `applications`
  MODIFY `id_application` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT untuk tabel `companies`
--
ALTER TABLE `companies`
  MODIFY `id_company` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `job_listings`
--
ALTER TABLE `job_listings`
  MODIFY `id_job` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT untuk tabel `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `applicants`
--
ALTER TABLE `applicants`
  ADD CONSTRAINT `applicants_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `applications`
--
ALTER TABLE `applications`
  ADD CONSTRAINT `applications_ibfk_1` FOREIGN KEY (`id_applicant`) REFERENCES `applicants` (`id_applicant`) ON DELETE CASCADE,
  ADD CONSTRAINT `applications_ibfk_2` FOREIGN KEY (`id_job`) REFERENCES `job_listings` (`id_job`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `companies`
--
ALTER TABLE `companies`
  ADD CONSTRAINT `companies_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `job_listings`
--
ALTER TABLE `job_listings`
  ADD CONSTRAINT `job_listings_ibfk_1` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE CASCADE;
COMMIT;

ALTER TABLE job_listings
ADD COLUMN slots INT(11) NOT NULL DEFAULT 1 AFTER location;


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_user INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message VARCHAR(255) NOT NULL,
    type ENUM('job_posted', 'application_received', 'application_status') NOT NULL,
    related_id INT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES users(id_user)
);

ALTER TABLE users MODIFY COLUMN role ENUM('applicant','company','admin') NOT NULL;

INSERT INTO users (email, password, role) 
VALUES ('admin@nemukerja.com', 'admin', 'admin');

