// ======================================================================================
// --- FUNGSI UTILITAS INTI (Universal) ---
// ======================================================================================

/**
 * Mengganti visibilitas field password dan ikon mata.
 * @param {string} id - ID dari input password.
 */
function togglePassword(id) {
    const pwd = document.getElementById(id);
    const eye = document.getElementById('eye-' + id);
    if (!pwd) return;
    if (pwd.type === 'password') {
        pwd.type = 'text';
        if (eye) { 
            eye.classList.remove('fa-eye');
            eye.classList.add('fa-eye-slash');
        }
    } else {
        pwd.type = 'password';
        if (eye) { 
            eye.classList.add('fa-eye');
            eye.classList.remove('fa-eye-slash');
        }
    }
}

/**
 * Placeholder (Tidak terpakai tapi ada di file lama)
 */
function enableSignUp() {
    const signUpBtn = document.getElementById("signup_btn");
    if (signUpBtn) {
        signUpBtn.disabled = false;
    }
}

/**
 * Mengonversi string ISO date menjadi format "time ago".
 */
function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

// ======================================================================================
// --- FUNGSI NOTIFIKASI (Sama seperti sebelumnya) ---
// ======================================================================================

/**
 * Mengambil Job ID dari Application ID (API baru)
 */
async function fetchJobIdFromApplication(applicationId) {
    try {
        const response = await fetch(`/api/get_job_id/${applicationId}`);
        if (!response.ok) return null;
        const data = await response.json();
        return data.job_id;
    } catch (error) {
        console.error('Error fetching job ID:', error);
        return null;
    }
}

/**
 * Menangani navigasi klik notifikasi.
 */
async function handleNotificationClick(notification) {
    const currentUserRole = window.currentUserRole || ''; 
    const relatedId = notification.related_id;

    if (relatedId === null || relatedId === 0 || isNaN(relatedId)) {
        console.log("Notifikasi tanpa ID terkait/Job dihapus, tidak ada navigasi.");
        return; 
    }
    
    switch(notification.type) {
        case 'job_posted':
            if (currentUserRole === 'applicant') {
                window.showJobDetail(relatedId);
            } else {
                window.location.href = '/dashboard';
            }
            break;
        
        case 'application_received':
            if (currentUserRole === 'company') {
                window.location.href = `/company/application/${relatedId}`;
            } else {
                window.location.href = '/dashboard';
            }
            break;
        
        case 'application_status':
            if (currentUserRole === 'applicant') {
                const jobId = await fetchJobIdFromApplication(relatedId);
                if (jobId) {
                    window.showJobDetail(jobId);
                } else {
                    alert('Job terkait sudah dihapus oleh perusahaan.');
                }
            } else {
                window.location.href = '/dashboard';
            }
            break;
            
        default:
            window.location.href = '/dashboard';
    }
}

/**
 * Menandai notifikasi sebagai 'read'.
 */
function markNotificationRead(notificationId, scope = '') {
    fetch(`/notifications/read/${notificationId}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json', }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications(); // Cukup panggil sekali
        }
    })
    .catch(error => console.error('Error marking notification read:', error));
}

/**
 * Menghapus semua notifikasi.
 */
function clearAllNotifications(scope = '') {
    if (!confirm('Are you sure you want to delete ALL notifications? This cannot be undone.')) {
        return;
    }
    fetch('/notifications/clear-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications(); // Cukup panggil sekali
        } else {
            alert('Error clearing notifications.');
        }
    })
    .catch(error => console.error('Error clearing all notifications:', error));
}

/**
 * Memuat notifikasi dari server.
 */
function loadNotifications() {
    fetch('/notifications')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(notifications => {
            updateNotificationUI(notifications);
        })
        .catch(error => console.error('Error loading notifications:', error));
}

/**
 * Memperbarui UI notifikasi (Dropdown).
 * DIPERBARUI: Disesuaikan untuk dropdown Tailwind baru.
 */
function updateNotificationUI(notifications) {
    const listContainer = document.getElementById('notification-menu'); 
    const badge = document.getElementById('notificationBadge');
    const badgeDot = document.getElementById('notificationBadgeDot');
    
    if (!listContainer || !badge || !badgeDot) return;
    
    const unreadCount = notifications.filter(n => !n.is_read).length;
    
    // Update badge
    if (unreadCount > 0) {
        badge.textContent = unreadCount;
        badge.classList.remove('tw-hidden');
        badgeDot.classList.remove('tw-hidden');
    } else {
        badge.classList.add('tw-hidden');
        badgeDot.classList.add('tw-hidden');
    }

    // Header Dropdown
    let html = `
        <div class="tw-p-3 tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-sm tw-font-medium tw-text-gray-900 dark:tw-text-white">
                <span data-i18n="notifications_en">Notifications</span>
                <span data-i18n="notifications_id" class="d-none">Notifikasi</span>
            </span>
            <div class="tw-flex tw-gap-2">
                <button class="tw-text-xs tw-text-blue-600 dark:tw-text-blue-400 hover:tw-underline" id="markAllReadBtn">
                    <span data-i18n="mark_all_read_en">Mark all read</span>
                </button>
                <button class="tw-text-xs tw-text-red-600 dark:tw-text-red-400 hover:tw-underline" id="clearAllBtn">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <hr class="tw-border-gray-200 dark:tw-border-gray-600 tw-m-0">
        <div id="notificationList" class="tw-max-h-80 tw-overflow-y-auto">
    `;

    if (!notifications || notifications.length === 0) {
        html += `
            <div class="tw-text-center tw-py-4 tw-text-sm tw-text-gray-500 dark:tw-text-gray-400">
                <span data-i18n="no_notifications_en">No notifications</span>
                <span data-i18n="no_notifications_id" class="d-none">Tidak ada notifikasi</span>
            </div>
        `;
    } else {
        notifications.forEach(notification => {
            const isReadClass = notification.is_read ? '' : 'tw-bg-gray-50 dark:tw-bg-gray-600';
            const timeAgo = getTimeAgo(notification.created_at);
            
            html += `
                <div class="notification-item tw-p-3 tw-cursor-pointer hover:tw-bg-gray-100 dark:hover:tw-bg-gray-500 ${isReadClass}" 
                     data-notification-id="${notification.id}" 
                     data-related-id="${notification.related_id}"
                     data-notification-type="${notification.type}">
                    <div class="tw-flex tw-w-full tw-justify-between tw-items-start">
                        <h6 class="tw-mb-1 tw-text-sm tw-font-medium tw-text-gray-900 dark:tw-text-white">${notification.title}</h6>
                        <small class="tw-text-xs tw-text-gray-500 dark:tw-text-gray-400 tw-flex-shrink-0 tw-ml-2">${timeAgo}</small>
                    </div>
                    <p class="tw-mb-0 tw-text-sm tw-text-gray-600 dark:tw-text-gray-300">${notification.message}</p>
                    ${!notification.is_read ? '<span class="tw-mt-1 tw-inline-block tw-text-xs tw-font-semibold tw-text-blue-600 dark:tw-text-blue-400">New</span>' : ''}
                </div>
            `;
        });
    }

    html += '</div>'; // Tutup #notificationList
    listContainer.innerHTML = html;

    // Terapkan bahasa saat ini ke konten yang baru dimuat
    const currentLang = localStorage.getItem('nk_lang') || 'en';
    window.toggleLang(currentLang);
}

// ======================================================================================
// --- FUNGSI MODAL (DIPERBARUI: Tanpa Bootstrap JS) ---
// ======================================================================================

/**
 * Helper untuk menerjemahkan konten modal
 */
function translateModalContent(modalElement, lang) {
    if (!modalElement) return;
    // ... (Logika ini tetap sama)
}

/**
 * DIPERBARUI: Fungsi Universal untuk mengambil detail pekerjaan dan mengisi modal.
 * Sekarang mengontrol modal menggunakan kelas Tailwind.
 * @param {number} jobId - ID pekerjaan.
 */
window.showJobDetail = function(jobId) {
    const modalElement = document.getElementById('jobDetailModal');
    if (!modalElement) {
        console.error('Modal element #jobDetailModal not found on this page.');
        return;
    }

    fetch(`/job/${jobId}`)
        .then(response => {
            // ... (Logika fetch dan error handling tetap sama)
            return response.json();
        })
        .then(job => {
            const modalTitleElement = document.getElementById('jobDetailTitle');
            const modalBodyElement = document.getElementById('jobDetailBody');
            const applyContainerElement = document.getElementById('applyButtonContainer');
            const currentLang = localStorage.getItem('nk_lang') || 'en';

            if (modalTitleElement) {
                // ... (Logika pengisian judul tetap sama)
            }

            if (modalBodyElement) {
                // ... (Logika pengisian modal body HTML tetap sama)
            }

            if (applyContainerElement) {
                // ... (Logika pembuatan tombol apply tetap sama)
            }

            // Terapkan terjemahan
            translateModalContent(modalElement, currentLang);
            
            // DIPERBARUI: Tampilkan modal menggunakan kelas Tailwind
            modalElement.classList.remove('tw-hidden');
            requestAnimationFrame(() => {
                modalElement.classList.remove('tw-opacity-0');
                // Asumsikan modal memiliki backdrop, kita juga tampilkan
                const backdrop = modalElement.querySelector('.modal-backdrop-custom');
                if(backdrop) backdrop.classList.remove('tw-opacity-0');
            });
        })
        .catch(error => {
            // ... (Logika error handling tetap sama)
        });

    // Helper untuk format gaji
    function formatSalary(min, max) {
        // ... (Logika format gaji tetap sama)
    }
}

/**
 * DIPERBARUI: Fungsi untuk halaman my_applications.
 * @param {number} jobId - ID pekerjaan.
 */
function showApplicationDetail(jobId) {
    const modalElement = document.getElementById('applicationDetailModal');
     if (!modalElement) {
        console.error('Modal element #applicationDetailModal not found on this page.');
        return;
    }

    fetch(`/job/${jobId}`)
        .then(response => response.json())
        .then(job => {
            // ... (Logika pengisian modal body tetap sama)

            // Terapkan terjemahan
            translateModalContent(modalElement, currentLang);

            // DIPERBARUI: Tampilkan modal menggunakan kelas Tailwind
            modalElement.classList.remove('tw-hidden');
            requestAnimationFrame(() => {
                modalElement.classList.remove('tw-opacity-0');
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading job details');
        });
}


// ======================================================================================
// --- EVENT LISTENER UTAMA (DOMContentLoaded) ---
// ======================================================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // --- BARU: Logika Tema Terang/Gelap ---
    const themeToggleButton = document.getElementById('theme-toggle-btn');
    const themeToggleButtonMobile = document.getElementById('theme-toggle-btn-mobile');
    
    function handleThemeToggle() {
        // Cek tema saat ini
        const isDark = document.documentElement.classList.toggle('dark');
        // Simpan preferensi
        if (isDark) {
            localStorage.setItem('color-theme', 'dark');
        } else {
            localStorage.setItem('color-theme', 'light');
        }
    }
    
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', handleThemeToggle);
    }
    if (themeToggleButtonMobile) {
        themeToggleButtonMobile.addEventListener('click', handleThemeToggle);
    }

    
    // --- BARU: Logika Dropdown Universal (Pengganti Bootstrap JS) ---
    const dropdownToggles = {
        'lang-menu-button': 'lang-menu',
        'notification-menu-button': 'notification-menu',
        'profile-menu-button': 'profile-menu',
    };

    // Fungsi untuk membuka/menutup dropdown
    function toggleDropdown(menuId) {
        const menu = document.getElementById(menuId);
        if (!menu) return;

        const isHidden = menu.classList.contains('tw-hidden');
        
        // Tutup semua dropdown lain
        Object.values(dropdownToggles).forEach(id => {
            if (id !== menuId) {
                const otherMenu = document.getElementById(id);
                if (otherMenu && !otherMenu.classList.contains('tw-hidden')) {
                    otherMenu.classList.add('tw-opacity-0', 'tw-scale-95');
                    setTimeout(() => otherMenu.classList.add('tw-hidden'), 150);
                }
            }
        });

        if (isHidden) {
            menu.classList.remove('tw-hidden');
            // 'requestAnimationFrame' untuk transisi 'enter'
            requestAnimationFrame(() => {
                menu.classList.remove('tw-opacity-0', 'tw-scale-95');
            });
        } else {
            menu.classList.add('tw-opacity-0', 'tw-scale-95');
            // 'setTimeout' untuk transisi 'leave'
            setTimeout(() => menu.classList.add('tw-hidden'), 150);
        }
    }

    // Tambahkan event listener ke semua tombol dropdown
    Object.keys(dropdownToggles).forEach(buttonId => {
        document.getElementById(buttonId)?.addEventListener('click', (e) => {
            e.stopPropagation(); // Hentikan event agar tidak ditangkap 'window'
            toggleDropdown(dropdownToggles[buttonId]);
        });
    });

    // --- BARU: Logika Menu Mobile ---
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = mobileMenu.classList.contains('tw-hidden');
            if (isHidden) {
                mobileMenu.classList.remove('tw-hidden');
                requestAnimationFrame(() => {
                    mobileMenu.classList.remove('tw-opacity-0', 'tw-scale-95');
                });
            } else {
                mobileMenu.classList.add('tw-opacity-0', 'tw-scale-95');
                setTimeout(() => mobileMenu.classList.add('tw-hidden'), 300);
            }
        });
    }

    // --- BARU: Klik di luar untuk menutup semua dropdown/menu ---
    window.addEventListener('click', () => {
        Object.values(dropdownToggles).forEach(id => {
            const menu = document.getElementById(id);
            if (menu && !menu.classList.contains('tw-hidden')) {
                menu.classList.add('tw-opacity-0', 'tw-scale-95');
                setTimeout(() => menu.classList.add('tw-hidden'), 150);
            }
        });
        
        if (mobileMenu && !mobileMenu.classList.contains('tw-hidden')) {
            mobileMenu.classList.add('tw-opacity-0', 'tw-scale-95');
            setTimeout(() => mobileMenu.classList.add('tw-hidden'), 300);
        }
    });

    // --- BARU: Logika Penutup Modal Universal ---
    // Menambahkan listener ke semua tombol yang punya atribut 'data-modal-close'
    document.querySelectorAll('[data-modal-close]').forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.getAttribute('data-modal-close');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('tw-opacity-0');
                setTimeout(() => modal.classList.add('tw-hidden'), 300); // Sesuaikan durasi transisi
            }
        });
    });


    // --- DIPERBARUI: Logika Bahasa (Sekarang menggunakan toggleDropdown) ---
    const LANG_KEY = 'nk_lang';
    
    window.toggleLang = function(lang) {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const id = el.getAttribute('data-i18n');
            if (id.endsWith('_en') || id.endsWith('_id')) {
                if (lang === 'en') {
                    if (id.endsWith('_en')) {
                        el.classList.remove('d-none', 'hidden');
                    } else if (id.endsWith('_id')) {
                        el.classList.add('d-none', 'hidden');
                    }
                } else if (lang === 'id') {
                    if (id.endsWith('_id')) {
                        el.classList.remove('d-none', 'hidden');
                    } else if (id.endsWith('_en')) {
                        el.classList.add('d-none', 'hidden');
                    }
                }
            }
        });
        
        const currentLabel = document.getElementById('current-lang');
        if (currentLabel) {
            currentLabel.textContent = (lang === 'id') ? 'Bahasa Indonesia' : 'English';
        }
        
        document.documentElement.lang = lang;
        updateFormPlaceholders(lang); // Panggil fungsi placeholder
        
        document.querySelectorAll('.lang-option').forEach(option => {
            option.classList.remove('active');
        });
        const activeOption = document.querySelector(`.lang-option[data-lang="${lang}"]`);
        if (activeOption) {
            activeOption.classList.add('active');
        }
    };
    
    // Inisialisasi bahasa saat memuat
    const savedLang = localStorage.getItem(LANG_KEY) || 'en';
    window.toggleLang(savedLang);
    
    // Tambahkan event listener ke opsi bahasa
    document.querySelectorAll('.lang-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); 
            const lang = this.getAttribute('data-lang');
            localStorage.setItem(LANG_KEY, lang);
            window.toggleLang(lang);
            toggleDropdown('lang-menu'); // Tutup menu setelah memilih
        });
    });


    // --- (Fungsionalitas Lama yang Dipertahankan) ---

    // Logika Flash Message (Diperbarui sedikit)
    const flashContainer = document.getElementById('flash-messages-container');
    if (flashContainer) {
        const AUTO_HIDE_MS = 4000;
        setTimeout(() => {
            flashContainer.classList.add('tw-opacity-0', 'tw-translate-y-[-10px]');
            setTimeout(() => {
                if (flashContainer) flashContainer.remove();
            }, 500);
        }, AUTO_HIDE_MS);
    }

    // Logika Notifikasi (Listener dipindahkan ke dropdown)
    let notificationCheckInterval;
    if (document.getElementById('notification-menu-button')) {
        loadNotifications(); // Muat saat awal
        
        // Setup polling
        notificationCheckInterval = setInterval(loadNotifications, 30000);

        // Event delegation untuk klik item notifikasi
        document.getElementById('notification-menu')?.addEventListener('click', function(e) {
            e.stopPropagation(); // Hentikan agar menu tidak tertutup
            
            // Logika untuk tombol 'Mark All Read' dan 'Clear All'
            if (e.target.id === 'markAllReadBtn') {
                fetch('/notifications/read-all', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', }
                })
                .then(response => response.json())
                .then(data => data.success && loadNotifications())
                .catch(error => console.error('Error marking all notifications read:', error));
            }
            if (e.target.id === 'clearAllBtn') {
                clearAllNotifications();
            }
            
            // Logika untuk klik item notifikasi
            let target = e.target.closest('.notification-item');
            if (target) {
                const notificationId = target.getAttribute('data-notification-id');
                const relatedId = target.getAttribute('data-related-id');
                const notificationType = target.getAttribute('data-notification-type');
                
                markNotificationRead(notificationId); 
                
                handleNotificationClick({
                    id: notificationId,
                    related_id: relatedId ? parseInt(relatedId) : null,
                    type: notificationType
                });
                toggleDropdown('notification-menu'); // Tutup menu setelah klik
            }
        });
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
        }
    });

    // Helper untuk Placeholder Form
    function updateFormPlaceholders(lang) {
        // ... (Logika ini tetap sama)
    }

    // Register Form Role Toggle (Tetap sama)
    const roleSelect = document.getElementById('role_select');
    if (roleSelect) {
        roleSelect.addEventListener('change', function() {
            var companyFields = document.getElementById('company_fields');
            if (this.value === 'company') {
                companyFields.style.display = 'block';
            } else {
                companyFields.style.display = 'none';
            }
        });
        roleSelect.dispatchEvent(new Event('change'));
    }

    // ApplyForm Character Counter dan Validasi (Tetap sama)
    const coverLetterTextarea = document.getElementById('cover_letter');
    const charCount = document.getElementById('charCount');
    const cvFileInput = document.getElementById('cv_file');
    const applyForm = document.getElementById('apply-form'); 

    if (coverLetterTextarea && charCount) {
        coverLetterTextarea.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = 'Character count: ' + count;
            
            if (count < 100) {
                charCount.className = 'text-danger small mt-1';
            } else if (count < 200) {
                charCount.className = 'text-warning small mt-1';
            } else {
                charCount.className = 'text-success small mt-1';
            }
        });
        coverLetterTextarea.dispatchEvent(new Event('input'));
    }
    
    // Client-side file validation (Pre-submit)
    if (cvFileInput) {
        cvFileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const maxSize = 10 * 1024 * 1024;
                if (!file.type.includes('pdf')) {
                    alert('Only PDF files are allowed.');
                    this.value = '';
                    return;
                }
                
                if (file.size > maxSize) {
                    alert('File size must be less than 10MB. Your file is too large.');
                    this.value = '';
                    return;
                }
            }
        });
    }
    
    // Enhanced form validation (On submit)
    if (applyForm) {
        applyForm.addEventListener('submit', function(e) {
            let isValid = true;
            let errorMessage = '';
            
            const coverLetter = document.getElementById('cover_letter').value;
            if (coverLetter.trim().length < 100) {
                isValid = false;
                errorMessage = 'Please write a more detailed cover letter (at least 100 characters).';
            }
            
            const cvFile = document.getElementById('cv_file').files[0];
            const maxSize = 10 * 1024 * 1024;

            if (!cvFile) {
                isValid = false;
                errorMessage = 'Please upload your CV file.';
            } else if (cvFile.size > maxSize) {
                isValid = false;
                errorMessage = 'File size must be less than 10MB. Your file is too large.';
            } else if (!cvFile.type.includes('pdf')) {
                isValid = false;
                errorMessage = 'Only PDF files are allowed.';
            }
            
            if (!isValid) {
                e.preventDefault();
                alert(errorMessage);
                return;
            }
            
            if (!confirm('Are you sure you want to submit your application? You cannot edit it after submission.')) {
                e.preventDefault();
            }
        });
    }


    // --- AddJobForm Logic (Textarea autoresize & validation) ---
    const textareas = document.querySelectorAll('.wrap textarea, .card-body textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        textarea.dispatchEvent(new Event('input'));
    });

    const addJobForm = document.querySelector('form[action$="/company/add-job"]');
    if (addJobForm) {
        addJobForm.addEventListener('submit', function(e) {
            const title = document.getElementById('title').value;
            const location = document.getElementById('location').value;
            const description = document.getElementById('description').value;
            
            const currentLang = localStorage.getItem('nk_lang') || 'en';
            const messages = {
                en: {
                    fill_fields: 'Please fill in all required fields.',
                    description_short: 'Please provide a more detailed job description (at least 20 characters).',
                    confirm: 'Are you sure you want to post this job?'
                },
                id: {
                    fill_fields: 'Harap isi semua bidang yang wajib diisi.',
                    description_short: 'Harap berikan deskripsi pekerjaan yang lebih detail (minimal 20 karakter).',
                    confirm: 'Apakah Anda yakin ingin memposting pekerjaan ini?'
                }
            };
            
            if (!title.trim() || !location.trim() || !description.trim()) {
                e.preventDefault();
                alert(messages[currentLang].fill_fields);
                return;
            }
            
            if (description.trim().length < 20) {
                e.preventDefault();
                alert(messages[currentLang].description_short);
                return;
            }
            
            if (!confirm(messages[currentLang].confirm)) {
                e.preventDefault();
            }
        });
    }

});