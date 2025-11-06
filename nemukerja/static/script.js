// ======================================================================================
// --- CORE UTILITY FUNCTIONS (Universal) ---
// ======================================================================================

/**
 * Toggles visibility of password fields and updates the eye icon.
 * @param {string} id - The ID of the password input field.
 */
function togglePassword(id) {
    var pwd = document.getElementById(id);
    var eye = document.getElementById('eye-' + id);
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
 * Placeholder function from original script.js.
 */
function enableSignUp() {
    const signUpBtn = document.getElementById("signup_btn");
    if (signUpBtn) {
        signUpBtn.disabled = false;
    }
}

// ======================================================================================
// --- NOTIFICATION SYSTEM FUNCTIONS (Universal) ---
// ======================================================================================

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

/**
 * Mengambil Job ID dari Application ID (API baru)
 * @param {number} applicationId
 * @returns {Promise<number|null>} Job ID atau null
 */
async function fetchJobIdFromApplication(applicationId) {
    try {
        const response = await fetch(`/api/get_job_id/${applicationId}`);
        // Jika API mengembalikan 404/403 (Job tidak ditemukan/Unauthorized), kita anggap Job ID tidak ada.
        if (!response.ok) return null;
        const data = await response.json();
        return data.job_id;
    } catch (error) {
        console.error('Error fetching job ID:', error);
        return null;
    }
}

/**
 * Handles navigation based on notification type and global user role.
 * @param {object} notification - The notification object.
 */
async function handleNotificationClick(notification) {
    const currentUserRole = window.currentUserRole || ''; 
    const relatedId = notification.related_id;

    // KASUS 1: Job Posting Dihapus (related_id = null atau 0) - FIX: Tidak ada navigasi dan tidak ada alert error.
    if (relatedId === null || relatedId === 0 || isNaN(relatedId)) {
        console.log("Notifikasi tanpa ID terkait/Job dihapus, tidak ada navigasi.");
        return; 
    }
    
    switch(notification.type) {
        case 'job_posted':
            // Pelamar: Job Posting Baru. relatedId = Job ID
            // Solusi: Tampilkan modal detail pekerjaan.
            if (currentUserRole === 'applicant') {
                window.showJobDetail(relatedId);
            } else {
                window.location.href = '/dashboard';
            }
            break;
        
        case 'application_received':
            // Perusahaan: Pelamar baru. relatedId = Application ID
            // Logika: Langsung ke halaman View Application spesifik.
            if (currentUserRole === 'company') {
                window.location.href = `/company/application/${relatedId}`;
            } else {
                window.location.href = '/dashboard';
            }
            break;
        
        case 'application_status':
            // Pelamar: Status lamaran diterima/ditolak. relatedId = Application ID
            // Logika: Fetch Job ID, lalu tampilkan detail job (modal).
            if (currentUserRole === 'applicant') {
                const jobId = await fetchJobIdFromApplication(relatedId);
                if (jobId) {
                    window.showJobDetail(jobId);
                } else {
                    // Job sudah dihapus setelah status diupdate.
                    alert('Job terkait sudah dihapus oleh perusahaan.');
                }
            } else {
                window.location.href = '/dashboard'; // Fallback
            }
            break;
            
        default:
            window.location.href = '/dashboard';
    }
}

/**
 * Marks a notification as read and reloads the UI.
 * @param {number} notificationId 
 * @param {string} scope - '' for desktop, 'Mobile' for mobile.
 */
function markNotificationRead(notificationId, scope = '') {
    fetch(`/notifications/read/${notificationId}`, { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications('');
            loadNotifications('Mobile'); 
        }
    })
    .catch(error => console.error('Error marking notification read:', error));
}

/**
 * Clears all notifications for the current user and reloads UI.
 * @param {string} scope - '' for desktop, 'Mobile' for mobile.
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
            loadNotifications('');
            loadNotifications('Mobile');
            alert('All notifications have been cleared.'); 
        } else {
            alert('Error clearing notifications.');
        }
    })
    .catch(error => console.error('Error clearing all notifications:', error));
}


/**
 * Fetches notifications and updates the UI for a specific scope.
 * @param {string} scope - '' for desktop, 'Mobile' for mobile.
 */
function loadNotifications(scope = '') {
    fetch('/notifications')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(notifications => {
            updateNotificationUI(notifications, scope);
        })
        .catch(error => console.error('Error loading notifications:', error));
}

function updateNotificationUI(notifications, scope = '') {
    const listId = `notificationList${scope}`;
    const badgeId = `notificationBadge${scope}`;
    const notificationList = document.getElementById(listId);
    const notificationBadge = document.getElementById(badgeId);
    
    if (!notificationList || !notificationBadge) return;
    
    const unreadCount = notifications.filter(n => !n.is_read).length;
    
    // Update badge
    if (unreadCount > 0) {
        notificationBadge.textContent = unreadCount;
        notificationBadge.style.display = 'block';
    } else {
        notificationBadge.style.display = 'none';
    }

    if (!notifications || notifications.length === 0) {
        notificationList.innerHTML = `
            <li class="text-center py-3 text-muted">
                <span data-i18n="no_notifications_en">No notifications</span>
                <span data-i18n="no_notifications_id" class="d-none">Tidak ada notifikasi</span>
            </li>
        `;
        return;
    }

    // Build notification list
    let html = '';
    notifications.forEach(notification => {
        const isReadClass = notification.is_read ? '' : 'bg-light';
        const timeAgo = getTimeAgo(notification.created_at);
        
        html += `
            <li>
                <div class="dropdown-item ${isReadClass} notification-item p-3" 
                     data-notification-id="${notification.id}" 
                     data-related-id="${notification.related_id}"
                     data-notification-type="${notification.type}"
                     style="cursor: pointer; border-bottom: 1px solid #f0f0f0;">
                    <div class="d-flex w-100 justify-content-between align-items-start">
                        <h6 class="mb-1" style="font-size: 0.9rem;">${notification.title}</h6>
                        <small class="text-muted">${timeAgo}</small>
                    </div>
                    <p class="mb-1 small text-muted">${notification.message}</p>
                    ${!notification.is_read ? '<span class="badge bg-primary btn-sm">New</span>' : ''}
                </div>
            </li>
        `;
    });
    notificationList.innerHTML = html;
}

// ======================================================================================
// --- JOB/APPLICATION DETAIL MODAL (Universal) ---
// ======================================================================================

/**
 * Helper to apply language translation to modal content
 * @param {HTMLElement} modalElement - The modal's main element.
 * @param {string} lang - The target language ('en' or 'id').
 */
function translateModalContent(modalElement, lang) {
    if (!modalElement) return;

    modalElement.querySelectorAll('[data-i18n]').forEach(el => {
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
}

/**
 * Universal function to fetch job details and populate a modal.
 * @param {number} jobId - The ID of the job listing.
 */
window.showJobDetail = function(jobId) {
    fetch(`/job/${jobId}`)
        .then(response => {
            if (response.status === 404) {
                throw new Error('JobNotFound');
            }
            if (!response.ok) {
                throw new Error('NetworkError');
            }
            return response.json();
        })
        .then(job => {
            const modalTitleElement = document.getElementById('jobDetailTitle');
            const modalBodyElement = document.getElementById('jobDetailBody');
            const applyContainerElement = document.getElementById('applyButtonContainer');
            const currentLang = localStorage.getItem('nk_lang') || 'en';

            if (modalTitleElement) {
                modalTitleElement.textContent = job.title;
            }

            // --- Create Modal Body Content (Universal) ---
            if (modalBodyElement) {
                modalBodyElement.innerHTML = `
                    <div class="space-y-6">
                        <div class="flex items-center text-gray-700 text-lg">
                            <i class="fas fa-building text-blue-500 mr-4 w-6"></i>
                            <span class="font-semibold mr-3">
                                <span data-i18n="modal_company_en">Company:</span>
                                <span data-i18n="modal_company_id" class="hidden">Perusahaan:</span>
                            </span>
                            <span>${job.company}</span>
                        </div>
                        <div class="flex items-center text-gray-700 text-lg">
                            <i class="fas fa-map-marker-alt text-green-500 mr-4 w-6"></i>
                            <span class="font-semibold mr-3">
                                <span data-i18n="modal_location_en">Location:</span>
                                <span data-i18n="modal_location_id" class="hidden">Lokasi:</span>
                            </span>
                            <span>${job.location}</span>
                        </div>
                        <div class="space-y-6">
                        <div class="flex items-center text-gray-700 text-lg">
                            <i class="fas fa-money-bill-wave text-yellow-500 mr-4 w-6"></i>
                            <span class="font-semibold mr-3">
                                <span data-i18n="modal_salary_en">Salary:</span>
                                <span data-i18n="modal_salary_id" class="hidden">Gaji:</span>
                            </span>
                            <span>${formatSalary(job.salary_min, job.salary_max)}</span>
                        </div>
                        <div class="flex items-center text-gray-700 text-lg">
                            <i class="fas fa-users text-purple-500 mr-4 w-6"></i>
                            <span class="font-semibold mr-3">
                                <span data-i18n="modal_available_slots_en">Available Slots:</span>
                                <span data-i18n="modal_available_slots_id" class="hidden">Kuota Tersedia:</span>
                            </span>
                            <span>${job.slots}</span>
                        </div>
                        <div class="flex items-center text-gray-700 text-lg">
                            <i class="fas fa-user-check text-orange-500 mr-4 w-6"></i>
                            <span class="font-semibold mr-3">
                                <span data-i18n="modal_current_applicants_en">Current Applicants:</span>
                                <span data-i18n="modal_current_applicants_id" class="hidden">Pelamar Saat Ini:</span>
                            </span>
                            <span>${job.applied_count}</span>
                        </div>
                        
                        <hr class="my-6 border-gray-300">
                        
                        <div>
                            <h6 class="font-semibold text-xl text-gray-800 mb-4 flex items-center">
                                <i class="fas fa-graduation-cap text-orange-500 mr-3"></i>
                                <span data-i18n="modal_qualifications_en">Qualifications</span>
                                <span data-i18n="modal_qualifications_id" class="hidden">Kualifikasi</span>
                            </h6>
                            <p class="text-gray-700 bg-gray-50 p-6 rounded-xl border border-gray-200 text-lg leading-relaxed">${job.qualifications.replace(/\n/g, '<br>')}</p>
                        </div>
                        
                        <hr class="my-6 border-gray-300">
                        
                        <div>
                            <h6 class="font-semibold text-xl text-gray-800 mb-4 flex items-center">
                                <i class="fas fa-tasks text-indigo-500 mr-3"></i>
                                <span data-i18n="modal_job_description_en">Job Description</span>
                                <span data-i18n="modal_job_description_id" class="hidden">Deskripsi Pekerjaan</span>
                            </h6>
                            <p class="text-gray-700 bg-gray-50 p-6 rounded-xl border border-gray-200 text-lg leading-relaxed">${job.description.replace(/\n/g, '<br>')}</p>
                        </div>
                    </div>
                `;
            }

            // --- Handle Apply Button (Relies on global variables from HTML) ---
            if (applyContainerElement) {
                const isAuthenticated = window.isAuthenticated === true;
                const userRole = window.currentUserRole; 

                let applyButton = '';
                
                // Cek apakah kuota penuh atau lowongan ditutup
                const isFull = job.applied_count >= job.slots;
                const isClosed = !job.is_open;
                
                if (isClosed) {
                     applyButton = `<button disabled class="bg-gray-400 text-white font-medium px-8 py-3 rounded-xl shadow-lg inline-flex items-center">
                        <i class="fas fa-times-circle mr-3"></i> Job Closed
                    </button>`;
                } else if (isFull) {
                     applyButton = `<button disabled class="bg-orange-500 text-white font-medium px-8 py-3 rounded-xl shadow-lg inline-flex items-center">
                        <i class="fas fa-exclamation-triangle mr-3"></i> Slots Full
                    </button>`;
                } else if (isAuthenticated && userRole === 'applicant') {
                    applyButton = `<a href="/apply/${job.id}" class="bg-blue-500 hover:bg-blue-600 text-white font-medium px-8 py-3 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg inline-flex items-center">
                        <i class="fas fa-paper-plane mr-3"></i>
                        <span data-i18n="modal_apply_now_en">Apply Now</span>
                        <span data-i18n="modal_apply_now_id" class="hidden">Lamar Sekarang</span>
                    </a>`;
                } else if (!isAuthenticated) {
                    applyButton = `<a href="/login" class="bg-blue-500 hover:bg-blue-600 text-white font-medium px-8 py-3 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg inline-flex items-center">
                        <i class="fas fa-sign-in-alt mr-3"></i>
                        <span data-i18n="modal_login_to_apply_en">Login to Apply</span>
                        <span data-i18n="modal_login_to_apply_id" class="hidden">Masuk untuk Lamar</span>
                    </a>`;
                } else {
                    applyButton = ''; 
                }


                applyContainerElement.innerHTML = applyButton;
            }

            const modalElement = document.getElementById('jobDetailModal');
            if (modalElement) {
                translateModalContent(modalElement, currentLang);
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        })
        .catch(error => {
            if (error.message === 'JobNotFound') {
                alert('Pekerjaan terkait telah dihapus oleh perusahaan.');
            } else {
                console.error('Error loading job details:', error);
                alert('Error loading job details'); 
            }
        });

        // Helper untuk format gaji
        function formatSalary(min, max) {
            if (!min && !max) return 'N/A';
            const formatter = new Intl.NumberFormat('id-ID', {
                style: 'currency',
                currency: 'IDR',
                minimumFractionDigits: 0
            });
            const minFormatted = formatter.format(min);
            const maxFormatted = formatter.format(max);
            
            if (min > 0 && max > 0 && min !== max) {
                return `${minFormatted} - ${maxFormatted}`;
            } else if (min > 0) {
                return `Min. ${minFormatted}`;
            } else if (max > 0) {
                return `Max. ${maxFormatted}`;
            }
            return 'N/A';
        }
}


/**
 * Function specific to my_applications.html to show a job's details in a different modal.
 * @param {number} jobId - The ID of the job listing.
 */
function showApplicationDetail(jobId) {
    fetch(`/job/${jobId}`)
        .then(response => response.json())
        .then(job => {
            const modalTitleElement = document.getElementById('applicationDetailTitle');
            const modalBodyElement = document.getElementById('applicationDetailBody');

            if (modalTitleElement) {
                 modalTitleElement.textContent = job.title;
            }
            if (modalBodyElement) {
                // This UI is specific to the "My Applications" page
                modalBodyElement.innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Company:</strong> ${job.company}</p>
                            <p><strong>Location:</strong> ${job.location}</p>
                            <p><strong>Available Slots:</strong> ${job.slots}</p>
                            <p><strong>Current Applicants:</strong> ${job.applied_count}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Status:</strong> 
                                <span class="badge bg-warning text-dark">
                                    <span data-i18n="my_applications_applied_en">Applied</span>
                                    <span data-i18n="my_applications_applied_id" class="d-none">Telah Dilamar</span>
                                </span>
                            </p>
                        </div>
                    </div>
                    <hr>
                    <h6>Qualifications:</h6>
                    <p>${job.qualifications.replace(/\n/g, '<br>')}</p>
                    <hr>
                    <h6>Job Description:</h6>
                    <p>${job.description.replace(/\n/g, '<br>')}</p>
                `;
            }

            const modal = new bootstrap.Modal(document.getElementById('applicationDetailModal'));
            modal.show();
            
            // Apply language to modal content
            const currentLang = localStorage.getItem('nk_lang') || 'en';
            translateModalContent(document.getElementById('applicationDetailModal'), currentLang);

        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading job details');
        });
}


// ======================================================================================
// --- MAIN INITIALIZATION & EVENT LISTENERS (Runs on DOMContentLoaded) ---
// ======================================================================================

document.addEventListener('DOMContentLoaded', function() {
    const LANG_KEY = 'nk_lang';
    const savedLang = localStorage.getItem(LANG_KEY) || 'en';
    
    // --- Helper for Auth/Form Placeholders ---
    function updateFormPlaceholders(lang) {
        const placeholders = {
            'en': {
                'name': 'Enter your full name',
                'email': 'Enter your email address',
                'phone': 'Enter your phone number',
                'password': 'Enter your password',
                'confirm_password': 'Confirm your password',
                'company_name': 'Enter company name',
                'description': 'Enter company description',
                'website': 'Enter company website (optional)',
                'cover_letter': 'Write your cover letter here...',
                'login_email': 'Enter your email',
                'login_password': 'Enter your password'
            },
            'id': {
                'name': 'Masukkan nama lengkap',
                'email': 'Masukkan alamat email',
                'phone': 'Masukkan nomor telepon',
                'password': 'Masukkan kata sandi',
                'confirm_password': 'Konfirmasi kata sandi',
                'company_name': 'Masukkan nama perusahaan',
                'description': 'Masukkan deskripsi perusahaan',
                'website': 'Masukkan situs web perusahaan (opsional)',
                'cover_letter': 'Tulis surat lamaran Anda di sini...',
                'login_email': 'Masukkan email Anda',
                'login_password': 'Masukkan kata sandi Anda'
            }
        };
        
        Object.keys(placeholders[lang]).forEach(field => {
            // Check original IDs and Login/Register specific IDs
            const element = document.getElementById(field);
            if (element) {
                element.placeholder = placeholders[lang][field];
            }
            // For login/register forms where IDs were different or dynamic
            if (field === 'email' || field === 'login_email') {
                const loginEmail = document.getElementById('email');
                if (loginEmail) loginEmail.placeholder = placeholders[lang].login_email;
            }
            if (field === 'password' || field === 'login_password') {
                const loginPassword = document.getElementById('login_password');
                if (loginPassword) loginPassword.placeholder = placeholders[lang].login_password;
            }
        });

        // Update placeholder for contact textarea
        const messageTextarea = document.getElementById('message');
        if (messageTextarea) {
            messageTextarea.placeholder = lang === 'en' ? 
                messageTextarea.getAttribute('data-i18n-placeholder-en') : 
                messageTextarea.getAttribute('data-i18n-placeholder-id');
        }
    }

    // --- Core Language Toggle (Made global in window scope) ---
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
        const currentLabelMobile = document.getElementById('current-lang-mobile');
        if (currentLabelMobile) {
            currentLabelMobile.textContent = (lang === 'id') ? 'Bahasa Indonesia' : 'English';
        }
        
        document.documentElement.lang = lang;
        updateFormPlaceholders(lang);
        
        document.querySelectorAll('.lang-option').forEach(option => {
            option.classList.remove('active');
        });
        const activeOption = document.querySelector(`.lang-option[data-lang="${lang}"]`);
        if (activeOption) {
            activeOption.classList.add('active');
        }

        // --- CUSTOM EVENT FOR MODAL/COMPONENT RE-TRANSLATION ---
        document.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { lang: lang } 
        }));
    };
    
    // Initialize with saved language
    window.toggleLang(savedLang);
    
    // Add click event listeners to language options
    document.querySelectorAll('.lang-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            localStorage.setItem(LANG_KEY, lang);
            window.toggleLang(lang);
        });
    });

    // --- Flash Message Logic ---
    const flashContainer = document.getElementById('flash-messages-container');
    if (flashContainer) {
        requestAnimationFrame(() => flashContainer.classList.add('show'));

        const msgs = flashContainer.querySelectorAll('.flash-message');
        msgs.forEach(msg => {
            const txt = (msg.textContent || '').trim().toLowerCase();
            if (txt.includes('please log in to access this page')) {
                msg.classList.add('persistent-login-alert');
                const closeBtn = msg.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.remove();
                }
            }
        });

        const AUTO_HIDE_MS = 3000;
        setTimeout(() => {
            flashContainer.style.transition = 'opacity 350ms ease, transform 300ms cubic-bezier(.2,.9,.2,1)';
            flashContainer.style.opacity = '0';
            flashContainer.style.transform = 'translateX(-50%) translateY(-10px)';
            setTimeout(() => {
                if (flashContainer && flashContainer.parentNode) flashContainer.remove();
            }, 400);
        }, AUTO_HIDE_MS);
    }

    window.clearPersistentLoginAlert = function() {
        const container = document.getElementById('flash-messages-container');
        if (!container) return;
        const persistent = container.querySelector('.persistent-login-alert');
        if (persistent) {
            persistent.remove();
        }
        if (container.children.length === 0 && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    };
    
    // --- NOTIFICATION LISTENERS (Desktop & Mobile) ---
    let notificationCheckInterval;

    if (document.getElementById('notificationDropdown') || document.getElementById('notificationDropdownMobile')) {
        // Initial load for both UIs
        loadNotifications(''); 
        loadNotifications('Mobile');

        // Setup polling
        notificationCheckInterval = setInterval(() => {
            loadNotifications('');
            loadNotifications('Mobile');
        }, 30000);

        // Event delegation for clicks on list items (Desktop)
        document.getElementById('notificationList')?.addEventListener('click', function(e) {
            let target = e.target;
            while (target && !target.classList.contains('notification-item')) {
                target = target.parentNode;
            }

            if (target && target.classList.contains('notification-item')) {
                const notificationId = target.getAttribute('data-notification-id');
                const relatedId = target.getAttribute('data-related-id');
                const notificationType = target.getAttribute('data-notification-type');
                
                markNotificationRead(notificationId, ''); 
                
                handleNotificationClick({
                    id: notificationId,
                    related_id: relatedId ? parseInt(relatedId) : null,
                    type: notificationType
                });
            }
        });
        
        // Event delegation for clicks on list items (Mobile)
        document.getElementById('notificationListMobile')?.addEventListener('click', function(e) {
            let target = e.target;
            while (target && !target.classList.contains('notification-item')) {
                target = target.parentNode;
            }

            if (target && target.classList.contains('notification-item')) {
                const notificationId = target.getAttribute('data-notification-id');
                const relatedId = target.getAttribute('data-related-id');
                const notificationType = target.getAttribute('data-notification-type');
                
                markNotificationRead(notificationId, 'Mobile'); 
                
                handleNotificationClick({
                    id: notificationId,
                    related_id: relatedId ? parseInt(relatedId) : null,
                    type: notificationType
                });
            }
        });
        
        // Mark all as read (Desktop)
        document.getElementById('markAllReadBtn')?.addEventListener('click', function(e) {
            e.stopPropagation();
            fetch('/notifications/read-all', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json', }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadNotifications('');
                    loadNotifications('Mobile');
                }
            })
            .catch(error => console.error('Error marking all notifications read:', error));
        });
        
        // Clear all (Desktop)
        document.getElementById('clearAllBtn')?.addEventListener('click', function(e) {
            e.stopPropagation();
            clearAllNotifications('');
        });

        // Mark all as read (Mobile)
        document.getElementById('markAllReadBtnMobile')?.addEventListener('click', function(e) {
            e.stopPropagation();
            fetch('/notifications/read-all', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json', }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadNotifications('');
                    loadNotifications('Mobile');
                }
            })
            .catch(error => console.error('Error marking all notifications read:', error));
        });
        
        // Clear all (Mobile)
        document.getElementById('clearAllBtnMobile')?.addEventListener('click', function(e) {
            e.stopPropagation();
            clearAllNotifications('Mobile');
        });
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
        }
    });

    // --- Register Form Role Toggle ---
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
    }
    
    // --- Register/Login Placeholder Rerun (For safety/initial state of eye icons) ---
    function updateAuthPlaceholderAndEye(lang) {
        updateFormPlaceholders(lang); // Rerun Placeholder logic

        // Update eye icon state (password fields on register form)
        ['signup_password', 'confirm_password', 'login_password'].forEach(function(id){
            var el = document.getElementById(id);
            var eye = document.getElementById('eye-' + id);
            if (!el || !eye) return;
            
            // Toggle eye icon class based on initial input type (usually password)
            if (el.type === 'text') {
                eye.classList.remove('fa-eye');
                eye.classList.add('fa-eye-slash');
            } else {
                eye.classList.remove('fa-eye-slash');
                eye.classList.add('fa-eye');
            }
        });
    }

    updateAuthPlaceholderAndEye(savedLang);

    // Listen for global language change event to update placeholders/eye icons
    document.addEventListener('languageChanged', function(e) {
        updateAuthPlaceholderAndEye(e.detail.lang);
    });

    // --- ApplyForm Character Counter and Client-side Validation ---
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