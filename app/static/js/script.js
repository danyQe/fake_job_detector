document.addEventListener('DOMContentLoaded', function() {
    // Authentication handling
    let authToken = localStorage.getItem('authToken');
    let tokenType = localStorage.getItem('tokenType');
    let isLoggedIn = false;

    // Function to show notifications
    function showNotification(message, type = 'error') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2">${type === 'error' ? '⚠️' : '✅'}</span>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // DOM elements
    const authButtons = document.getElementById('auth-buttons');
    const userInfo = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');
    const loginButton = document.getElementById('login-button');
    const registerButton = document.getElementById('register-button');
    const logoutButton = document.getElementById('logout-button');
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');
    const switchToRegister = document.getElementById('switch-to-register');
    const switchToLogin = document.getElementById('switch-to-login');
    const analyzeForm = document.getElementById('analyze-form');

    // API endpoints
    const API_BASE_URL = window.location.origin;
    const API_ENDPOINTS = {
        login: `${API_BASE_URL}/auth/token`,
        register: `${API_BASE_URL}/auth/register`,
        profile: `${API_BASE_URL}/auth/me`,
        jobHistory: `${API_BASE_URL}/jobs/history`,
        resumeHistory: `${API_BASE_URL}/resumes/history`,
        analyzeJob: `${API_BASE_URL}/jobs/analyze`,
        generateResume: `${API_BASE_URL}/resumes/generate`,
        parsePdf: `${API_BASE_URL}/resumes/parse-pdf`,
        downloadResume:`${API_BASE_URL}/resumes/download`
    };

    // Check if user is logged in
    function checkAuthentication() {
        // Get the token from localStorage
        const storedToken = localStorage.getItem('authToken');
        const storedTokenType = localStorage.getItem('tokenType');
        
        if (storedToken && storedTokenType) {
            // Update global variables
            authToken = storedToken;
            tokenType = storedTokenType;
            
            // Show loading state
            authButtons.classList.add('hidden');
            userInfo.classList.remove('hidden');
            usernameDisplay.textContent = 'Loading...';
            
            // Verify the token with the server
            fetch(API_ENDPOINTS.profile, {
                headers: {
                    'Authorization': `${tokenType} ${authToken}`
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else if (response.status === 401) {
                    // Token is invalid or expired
                    logoutUser();
                    return null;
                } else {
                    throw new Error('Authentication failed');
                }
            })
            .then(user => {
                if (user) {
                    isLoggedIn = true;
                usernameDisplay.textContent = user.username || user.email;
                } else {
                    isLoggedIn = false;
                    authButtons.classList.remove('hidden');
                    userInfo.classList.add('hidden');
                }
            })
            .catch(error => {
                console.error('Error fetching profile:', error);
                logoutUser();
            });
        } else {
            isLoggedIn = false;
            authButtons.classList.remove('hidden');
            userInfo.classList.add('hidden');
        }
    }

    // Login user
    function loginUser(email, password) {
        loginError.classList.add('hidden');
        
        if (!email || !password) {
            loginError.textContent = 'Please enter both email and password';
            loginError.classList.remove('hidden');
            return;
        }
        
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        fetch(API_ENDPOINTS.login, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else if (response.status === 401) {
                throw new Error('Invalid email or password');
            } else {
                throw new Error('Login failed. Please try again later.');
            }
        })
        .then(data => {
            // Store the token in localStorage
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('tokenType', data.token_type);
            
            // Update the global variables
            authToken = data.access_token;
            tokenType = data.token_type;
            
            // Close the login modal
            loginModal.style.display = 'none';
            
            // Reset the form
            loginForm.reset();
            
            // Update the UI
            checkAuthentication();
        })
        .catch(error => {
            loginError.textContent = error.message;
            loginError.classList.remove('hidden');
        });
    }

    // Register user
    function registerUser(email, username, fullName, password) {
        registerError.classList.add('hidden');
        
        // Basic validation
        if (!email || !username || !fullName || !password) {
            registerError.textContent = 'All fields are required';
            registerError.classList.remove('hidden');
            return;
        }
        
        if (password.length < 8) {
            registerError.textContent = 'Password must be at least 8 characters long';
            registerError.classList.remove('hidden');
            return;
        }
        
        fetch(API_ENDPOINTS.register, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                username: username,
                full_name: fullName,
                password: password
            })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return response.json().then(err => {
                    throw new Error(err.detail || 'Registration failed. Please try again.');
                });
            }
        })
        .then(data => {
            registerModal.style.display = 'none';
            loginModal.style.display = 'block';
            registerForm.reset();
            
            // Show success message in login form
            loginError.textContent = 'Registration successful! Please login with your credentials.';
            loginError.classList.remove('hidden');
            loginError.classList.remove('text-red-600');
            loginError.classList.add('text-green-600');
            
            // Populate email field for convenience
            document.getElementById('login-email').value = email;
            document.getElementById('login-password').focus();
        })
        .catch(error => {
            registerError.textContent = error.message;
            registerError.classList.remove('hidden');
        });
    }

    // Logout user
    function logoutUser() {
        // Clear localStorage
        localStorage.removeItem('authToken');
        localStorage.removeItem('tokenType');
        
        // Reset global variables
        authToken = null;
        tokenType = null;
        isLoggedIn = false;
        
        // Update UI
        authButtons.classList.remove('hidden');
        userInfo.classList.add('hidden');
        usernameDisplay.textContent = '';
    }

    // Event listeners for authentication
    loginButton.addEventListener('click', () => {
        // Reset error messages
        loginError.classList.add('hidden');
        loginError.classList.remove('text-green-600');
        loginError.classList.add('text-red-600');
        loginForm.reset();
        loginModal.style.display = 'block';
        document.getElementById('login-email').focus();
    });

    registerButton.addEventListener('click', () => {
        registerError.classList.add('hidden');
        registerForm.reset();
        registerModal.style.display = 'block';
        document.getElementById('register-email').focus();
    });

    logoutButton.addEventListener('click', () => {
        logoutUser();
    });

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        loginUser(email, password);
    });

    registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('register-email').value;
        const username = document.getElementById('register-username').value;
        const fullName = document.getElementById('register-fullname').value;
        const password = document.getElementById('register-password').value;
        registerUser(email, username, fullName, password);
    });

    switchToRegister.addEventListener('click', (e) => {
        e.preventDefault();
        loginModal.style.display = 'none';
        registerModal.style.display = 'block';
        document.getElementById('register-email').focus();
    });

    switchToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        registerModal.style.display = 'none';
        loginModal.style.display = 'block';
        document.getElementById('login-email').focus();
    });

    // Close modals when the user clicks the close button
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
        });
    });

    // Close modals when the user clicks outside the modal content
    window.addEventListener('click', (event) => {
        document.querySelectorAll('.modal').forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Keyboard accessibility for modals
    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                if (modal.style.display === 'block') {
                    modal.style.display = 'none';
                }
            });
        }
    });

    // Initialize authentication check
    checkAuthentication();

    // Toggle text input visibility
    const useTextCheckbox = document.getElementById('use-text');
    const textInputContainer = document.getElementById('text-input-container');
    const jobUrlInput = document.getElementById('job-url');
    const jobTextInput = document.getElementById('job-text');

    useTextCheckbox.addEventListener('change', function() {
        if (this.checked) {
            textInputContainer.classList.remove('hidden');
            jobUrlInput.required = false;
            jobTextInput.required = true;
        } else {
            textInputContainer.classList.add('hidden');
            jobUrlInput.required = true;
            jobTextInput.required = false;
        }
    });

    // Analyze job
    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const jobUrl = document.getElementById('job-url').value.trim();
        const jobText = document.getElementById('job-text').value.trim();
        const useText = document.getElementById('use-text').checked;
        const textInputContainer = document.getElementById('text-input-container');
        
        if (!useText && !jobUrl) {
            alert('Please enter a job posting URL');
            return;
        }
        
        if (useText && !jobText) {
            alert('Please enter job posting details');
            return;
        }
        
        if (!isLoggedIn) {
            loginModal.style.display = 'block';
            return;
        }
        
        // Show loader and hide results
        document.getElementById('loader').classList.remove('hidden');
        document.getElementById('result-card').classList.add('hidden');
        
        try {
            const requestBody = {
                useBrowser: false
            };
            
            if (useText) {
                requestBody.text = jobText;
            } else {
                requestBody.url = jobUrl;
            }
            
            const response = await fetch(API_ENDPOINTS.analyzeJob, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `${tokenType} ${authToken}`
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail)) {
                        throw new Error(errorData.detail.map(err => err.msg).join(', '));
                    } else {
                        // Check if it's a LinkedIn URL error
                        if (errorData.detail.includes('LinkedIn job postings require login')) {
                            // Show the text input container
                            textInputContainer.classList.remove('hidden');
                            document.getElementById('use-text').checked = true;
                            document.getElementById('job-text').required = true;
                            document.getElementById('job-url').required = false;
                            // Show the error message
                            alert(errorData.detail);
                            return;
                        }
                        throw new Error(errorData.detail);
                    }
                }
                throw new Error('Failed to analyze job');
            }
            
            const result = await response.json();
            
            // Check if job is blacklisted
            if (result.is_blacklisted) {
                const proceed = confirm(
                    `⚠️ WARNING: This job posting has been previously reported as fake by ${result.report_count || 1} users.\n\n` +
                    `Reason: ${result.reasoning}\n\n` +
                    `Do you still want to proceed with the analysis?`
                );
                
                if (!proceed) {
                    document.getElementById('loader').classList.add('hidden');
                    return;
                }
            }
            
            showResults(result);
        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing job posting: ' + error.message);
        } finally {
            document.getElementById('loader').classList.add('hidden');
        }
    });

    // Function to display results
    function showResults(result) {
        const resultCard = document.getElementById('result-card');
        const jobTitle = document.getElementById('job-title');
        const jobUrlDisplay = document.getElementById('job-url-display');
        const resultAlert = document.getElementById('result-alert');
        const resultIcon = document.getElementById('result-icon');
        const resultHeading = document.getElementById('result-heading');
        const resultText = document.getElementById('result-text');
        const confidenceBar = document.getElementById('confidence-bar');
        const reasoningText = document.getElementById('reasoning-text');
        const processingTime = document.getElementById('processing-time');
        const resumeSection = document.getElementById('resume-section');
        
        // Update the job ID handling
        window.lastAnalyzedJobId = parseInt(result.id);  // Use id instead of job_id and parse as integer
        console.log('Stored job ID for resume generation:', window.lastAnalyzedJobId);
        
        // Store job details for resume generation
        window.lastAnalyzedJobDetails = {
            job_title: result.job_title || '',
            description: result.job_content || '',
            company: result.company_name || '',
            location: '',
            reasoning: result.reasoning || '',
            requirements: [],
            skills: [],
            salary_range: '',
            job_type: '',
            experience_level: ''
        };
        console.log('Stored job details:', window.lastAnalyzedJobDetails);
        
        // Update display
        jobTitle.textContent = result.job_title || 'Job Analysis';
        jobUrlDisplay.textContent = result.url;
        jobUrlDisplay.href = result.url;
        
        // Set result styling based on prediction
        if (result.is_fake) {
            resultAlert.className = 'p-4 rounded-lg bg-red-50';
            resultIcon.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-red-500"></i>';
            resultHeading.textContent = 'Potential Scam Detected';
            resultHeading.className = 'text-xl font-semibold mb-2 text-red-700';
            resultText.textContent = `This job posting has been flagged as potentially fraudulent with ${result.confidence.toFixed(1)}% confidence.`;
            confidenceBar.className = 'h-2 rounded-full bg-red-500 transition-all duration-500';
            resumeSection.classList.add('hidden');
        } else {
            resultAlert.className = 'p-4 rounded-lg bg-green-50';
            resultIcon.innerHTML = '<i class="bi bi-check-circle-fill text-green-500"></i>';
            resultHeading.textContent = 'Legitimate Job Detected';
            resultHeading.className = 'text-xl font-semibold mb-2 text-green-700';
            resultText.textContent = `This job posting appears to be legitimate with ${result.confidence.toFixed(1)}% confidence.`;
            confidenceBar.className = 'h-2 rounded-full bg-green-500 transition-all duration-500';
            resumeSection.classList.remove('hidden');
        }
        
        // Set confidence bar width
        confidenceBar.style.width = `${result.confidence}%`;
        
        // Update reasoning
        reasoningText.innerHTML = marked.parse(result.reasoning || '');
        
        // Update processing time
        processingTime.textContent = result.processing_time ? result.processing_time.toFixed(2) : '0.00';
        
        // Show result card
        resultCard.classList.remove('hidden');
        
        // Scroll to result
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // History feature
    const jobHistoryList = document.getElementById('job-history-list');
    const resumeHistoryList = document.getElementById('resume-history-list');
    const historyModal = document.getElementById('history-modal');
    const historyButton = document.getElementById('history-button');

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all tabs
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-indigo-100', 'border-b-2', 'border-indigo-600');
                btn.setAttribute('aria-selected', 'false');
            });
            
            // Add active class to clicked tab
            button.classList.add('bg-indigo-100', 'border-b-2', 'border-indigo-600');
            button.setAttribute('aria-selected', 'true');
            
            // Hide all tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            // Show content for active tab
            const tabId = button.getAttribute('data-tab');
            const tabContent = document.getElementById(tabId);
            tabContent.classList.remove('hidden');
            
            // Load correct data
            if (tabId === 'job-history') {
                loadJobHistory();
            } else if (tabId === 'resume-history') {
                loadResumeHistory();
            }
        });
    });

    // Show history modal when history button is clicked
    historyButton.addEventListener('click', () => {
        if (!isLoggedIn) {
            loginModal.style.display = 'block';
            return;
        }
        
        historyModal.style.display = 'block';
        loadJobHistory();
    });

    // Load job analysis history
    function loadJobHistory() {
        jobHistoryList.innerHTML = '<p class="text-center text-gray-500">Loading job history...</p>';
        
        fetch(API_ENDPOINTS.jobHistory, {
            headers: {
                'Authorization': `${tokenType} ${authToken}`
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Failed to load job history');
            }
        })
        .then(jobs => {
            if (jobs.length === 0) {
                jobHistoryList.innerHTML = '<p class="text-center text-gray-500">No job analyses found</p>';
                return;
            }
            
            jobHistoryList.innerHTML = '';
            jobs.forEach(job => {
                const jobCard = document.createElement('div');
                jobCard.className = 'bg-white p-4 rounded-lg shadow border border-gray-200 hover:shadow-md transition-shadow';
                
                const statusClass = job.is_fake ? 'text-red-600' : 'text-green-600';
                const statusIcon = job.is_fake ? 
                    '<i class="bi bi-exclamation-triangle-fill"></i>' : 
                    '<i class="bi bi-check-circle-fill"></i>';
                
                jobCard.innerHTML = `
                    <div class="flex flex-col sm:flex-row justify-between sm:items-start gap-2">
                        <div>
                            <h3 class="font-semibold text-lg">${job.job_title || 'Job Analysis'}</h3>
                            <p class="text-sm text-gray-600 truncate">${job.job_url}</p>
                        </div>
                        <span class="${statusClass} font-semibold flex items-center whitespace-nowrap">
                            ${statusIcon} ${job.is_fake ? 'Fake' : 'Legitimate'}
                        </span>
                    </div>
                    <div class="mt-2 flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                        <p class="text-sm text-gray-500">${new Date(job.created_at).toLocaleString()}</p>
                        <div class="flex items-center gap-2">
                            <button class="text-indigo-600 hover:text-indigo-800 view-job-btn" data-id="${job.id}" aria-label="View details for this job analysis">
                                View Details
                            </button>
                            <button class="delete-job-btn text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1" data-id="${job.id}" aria-label="Delete this job analysis">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                
                jobHistoryList.appendChild(jobCard);
                
                // Add event listener to view button
                jobCard.querySelector('.view-job-btn').addEventListener('click', () => {
                    // Load job analysis details and display
                    fetch(`${API_BASE_URL}/jobs/${job.id}`, {
                        headers: {
                            'Authorization': `${tokenType} ${authToken}`
                        }
                    })
                    .then(response => response.json())
                    .then(jobDetail => {
                        // Create a result object in the expected format
                        const result = {
                            id: job.id,
                            job_title: jobDetail.job_title,
                            url: jobDetail.job_url,
                            is_fake: jobDetail.is_fake,
                            confidence: jobDetail.confidence,
                            reasoning: jobDetail.reasoning,
                            processing_time: 0 // Not available in history
                        };
                        
                        // Display the results
                        showResults(result);
                        historyModal.style.display = 'none';
                    })
                    .catch(error => {
                        console.error('Error loading job details:', error);
                        alert('Failed to load job details. Please try again.');
                    });
                });

                // Add event listener to delete button
                jobCard.querySelector('.delete-job-btn').addEventListener('click', () => {
                    if (confirm('Are you sure you want to delete this job analysis?')) {
                        deleteJobAnalysis(job.id);
                    }
                });
            });
        })
        .catch(error => {
            console.error('Error loading job history:', error);
            jobHistoryList.innerHTML = '<p class="text-center text-red-500">Error loading job history</p>';
        });
    }

    // Load resume history
    function loadResumeHistory() {
        resumeHistoryList.innerHTML = '<p class="text-center text-gray-500">Loading resume history...</p>';
        
        fetch(API_ENDPOINTS.resumeHistory, {
            headers: {
                'Authorization': `${tokenType} ${authToken}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load resume history (${response.status})`);
            }
            return response.json();
        })
        .then(resumes => {
            if (!resumes || resumes.length === 0) {
                resumeHistoryList.innerHTML = '<p class="text-center text-gray-500">No resumes found</p>';
                return;
            }
            
            resumeHistoryList.innerHTML = '';
            resumes.forEach(resume => {
                const resumeCard = document.createElement('div');
                resumeCard.className = 'bg-white p-4 rounded-lg shadow border border-gray-200 hover:shadow-md transition-shadow';
                
                const fullName = resume.resume_data?.fullName || 'Resume';
                const jobTitle = resume.resume_data?.title || '';
                const format = resume.format || 'pdf';
                
                resumeCard.innerHTML = `
                    <div class="flex flex-col sm:flex-row justify-between sm:items-start gap-2">
                        <div>
                            <h3 class="font-semibold text-lg">${fullName}</h3>
                            <p class="text-sm text-gray-600">${jobTitle}</p>
                        </div>
                        <span class="text-indigo-600 font-semibold">${format.toUpperCase()}</span>
                    </div>
                    <div class="mt-2 flex flex-col sm:flex-row justify-between sm:items-center gap-2">
                        <p class="text-sm text-gray-500">${new Date(resume.created_at).toLocaleString()}</p>
                        <div class="flex items-center gap-2">
                            <button class="text-indigo-600 hover:text-indigo-800 download-resume-btn" data-id="${resume.id}" data-format="${format}" aria-label="Download this resume">
                                Download
                            </button>
                            <button class="delete-resume-btn text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1" data-id="${resume.id}" aria-label="Delete this resume">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                
                resumeHistoryList.appendChild(resumeCard);
                
                // Add event listener to download button using the new download function
                resumeCard.querySelector('.download-resume-btn').addEventListener('click', async () => {
                    const resumeId = resume.id;
                    const format = resume.format || 'pdf';

                    // Show loading state
                        const button = resumeCard.querySelector('.download-resume-btn');
                        const originalText = button.textContent;
                        button.textContent = 'Downloading...';
                        button.disabled = true;

                    try {
                        // Use the improved download function
                        await downloadResume(resumeId, format);
                    } finally {
                        // Restore button state
                        button.textContent = originalText;
                            button.disabled = false;
                    }
                });

                // Add event listener to delete button (unchanged)
                resumeCard.querySelector('.delete-resume-btn').addEventListener('click', () => {
                    if (confirm('Are you sure you want to delete this resume?')) {
                        deleteResume(resume.id);
                    }
                });
            });
        })
        .catch(error => {
            console.error('Error loading resume history:', error);
            resumeHistoryList.innerHTML = `
                <div class="text-center text-red-500">
                    <p class="font-semibold">Error loading resume history</p>
                    <p class="text-sm mt-2">${error.message}</p>
                    <p class="text-xs mt-1">Please try again later or contact support if the problem persists.</p>
                </div>
            `;
        });
    }

    // Dynamic form handling for work experience, education, and certifications
    function setupDynamicFormFields() {
        // Add experience entry
        document.getElementById('add-experience')?.addEventListener('click', function() {
            const container = document.getElementById('experience-container');
            if (!container) return; // Make sure container exists
            
            const entries = container.getElementsByClassName('experience-entry');
            if (!entries || entries.length === 0) {
                console.error('No experience entries found to clone');
                return;
            }
            
            const newEntry = entries[0].cloneNode(true);
            const index = entries.length;
            
            // Update IDs and name attributes
            newEntry.querySelectorAll('input, textarea').forEach(input => {
                const oldName = input.name;
                const oldId = input.id;
                
                input.value = '';
                input.name = input.name.replace('[0]', `[${index}]`);
                input.id = input.id.replace('-0-', `-${index}-`);
                
                // Update associated label
                const label = newEntry.querySelector(`label[for="${oldId}"]`);
                if (label) {
                    label.setAttribute('for', input.id);
                }
            });
            
            // Add remove button if it's not the first entry
            if (index > 0) {
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'text-red-600 hover:text-red-700 text-sm font-medium mt-2 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1';
                removeBtn.innerHTML = '<i class="bi bi-trash mr-1"></i> Remove Entry';
                removeBtn.setAttribute('aria-label', 'Remove this experience entry');
                removeBtn.onclick = function() {
                    newEntry.remove();
                };
                newEntry.appendChild(removeBtn);
            }
            
            container.appendChild(newEntry);

            // Add event listeners to new entries
            newEntry.querySelectorAll('input, textarea').forEach(input => {
                input.addEventListener('input', () => {
                    input.classList.remove('error');
                    const errorMessage = input.parentElement.querySelector('.error-message');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                });
            });
        });

        // Add education entry
        document.getElementById('add-education')?.addEventListener('click', function() {
            const container = document.getElementById('education-container');
            if (!container) return; // Make sure container exists
            
            const entries = container.getElementsByClassName('education-entry');
            if (!entries || entries.length === 0) {
                console.error('No education entries found to clone');
                return;
            }
            
            const newEntry = entries[0].cloneNode(true);
            const index = entries.length;
            
            newEntry.querySelectorAll('input').forEach(input => {
                const oldId = input.id;
                
                input.value = '';
                input.name = input.name.replace('[0]', `[${index}]`);
                input.id = input.id.replace('-0-', `-${index}-`);
                
                // Update associated label
                const label = newEntry.querySelector(`label[for="${oldId}"]`);
                if (label) {
                    label.setAttribute('for', input.id);
                }
            });
            
            if (index > 0) {
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'text-red-600 hover:text-red-700 text-sm font-medium mt-2 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1';
                removeBtn.innerHTML = '<i class="bi bi-trash mr-1"></i> Remove Entry';
                removeBtn.setAttribute('aria-label', 'Remove this education entry');
                removeBtn.onclick = function() {
                    newEntry.remove();
                };
                newEntry.appendChild(removeBtn);
            }
            
            container.appendChild(newEntry);

            // Add event listeners to new entries
            newEntry.querySelectorAll('input').forEach(input => {
                input.addEventListener('input', () => {
                    input.classList.remove('error');
                    const errorMessage = input.parentElement.querySelector('.error-message');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                });
            });
        });

        // Add certification entry
        document.getElementById('add-certification')?.addEventListener('click', function() {
            const container = document.getElementById('certification-container');
            if (!container) return; // Make sure container exists
            
            const entries = container.getElementsByClassName('certification-entry');
            if (!entries || entries.length === 0) {
                console.error('No certification entries found to clone');
                return;
            }
            
            const newEntry = entries[0].cloneNode(true);
            const index = entries.length;
            
            newEntry.querySelectorAll('input').forEach(input => {
                const oldId = input.id;
                
                input.value = '';
                input.name = input.name.replace('[0]', `[${index}]`);
                input.id = input.id.replace('-0-', `-${index}-`);
                
                // Update associated label
                const label = newEntry.querySelector(`label[for="${oldId}"]`);
                if (label) {
                    label.setAttribute('for', input.id);
                }
            });
            
            if (index > 0) {
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'text-red-600 hover:text-red-700 text-sm font-medium mt-2 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1';
                removeBtn.innerHTML = '<i class="bi bi-trash mr-1"></i> Remove Entry';
                removeBtn.setAttribute('aria-label', 'Remove this certification entry');
                removeBtn.onclick = function() {
                    newEntry.remove();
                };
                newEntry.appendChild(removeBtn);
            }
            
            container.appendChild(newEntry);

            // Add event listeners to new entries
            newEntry.querySelectorAll('input').forEach(input => {
                input.addEventListener('input', () => {
                    input.classList.remove('error');
                    const errorMessage = input.parentElement.querySelector('.error-message');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                });
            });
        });
    }

    setupDynamicFormFields();

    // Add Fresher checkbox functionality to hide work experience
    const fresherCheckbox = document.getElementById('isFresher');
    const experienceSection = document.getElementById('experience-section');
    
    if (fresherCheckbox && experienceSection) {
        fresherCheckbox.addEventListener('change', function() {
            if (this.checked) {
                experienceSection.classList.add('hidden');
                
                // Clear all experience entries except the first one
                const experienceContainer = document.getElementById('experience-container');
                const entries = experienceContainer.querySelectorAll('.experience-entry');
                
                // Clear the first entry's inputs
                if (entries.length > 0) {
                    const firstEntry = entries[0];
                    firstEntry.querySelectorAll('input, textarea').forEach(input => {
                        input.value = '';
                        // Remove required attribute
                        if (input.hasAttribute('required')) {
                            input.removeAttribute('required');
                        }
                    });
                }
                
                // Remove additional entries
                for (let i = 1; i < entries.length; i++) {
                    entries[i].remove();
                }
                
                // Double-check specifically for textarea to ensure required attribute is removed
                const textareas = experienceContainer.querySelectorAll('textarea[required]');
                textareas.forEach(textarea => {
                    textarea.removeAttribute('required');
                });
            } else {
                // Show the experience section
                experienceSection.classList.remove('hidden');
                
                // Re-add required attribute to inputs in first experience entry
                const experienceContainer = document.getElementById('experience-container');
                const firstEntry = experienceContainer.querySelector('.experience-entry');
                
                if (firstEntry) {
                    // Re-add required attribute to company, title, startDate, and description
                    const reqFields = [
                        firstEntry.querySelector('[name$=".company"]'),
                        firstEntry.querySelector('[name$=".title"]'),
                        firstEntry.querySelector('[name$=".startDate"]'),
                        firstEntry.querySelector('[name$=".description"]')
                    ];
                    
                    reqFields.forEach(field => {
                        if (field) {
                            field.setAttribute('required', '');
                        }
                    });
                }
            }
        });
    }

    // Template preview functionality
    const templateSelect = document.getElementById('template');
    const templatePreview = document.getElementById('template-preview');
    
    // Only initialize template preview if both elements exist
    if (templateSelect && templatePreview) {
        // Template preview styles
        const templateStyles = {
            modern: {
                name: "Modern Professional",
                description: "Clean and contemporary design with clear section separation",
                preview: `
                    <div class="text-left">
                        <div class="text-center mb-4 pb-2 border-b-2 border-gray-300">
                            <div class="text-2xl font-bold text-gray-800">John Doe</div>
                            <div class="text-lg text-gray-600">Software Engineer</div>
                            <div class="text-sm text-gray-500">john@example.com | (555) 123-4567 | New York, NY</div>
                        </div>
                        <div class="space-y-3">
                            <div>
                                <div class="text-sm font-bold text-gray-800 uppercase tracking-wide">Professional Summary</div>
                                <div class="text-sm text-gray-600">Experienced software engineer with expertise in...</div>
                            </div>
                            <div>
                                <div class="text-sm font-bold text-gray-800 uppercase tracking-wide">Skills</div>
                                <div class="text-sm text-gray-600">JavaScript, Python, React, Node.js</div>
                            </div>
                        </div>
                    </div>
                `
            },
            classic: {
                name: "Classic Traditional",
                description: "Timeless and professional layout with emphasis on readability",
                preview: `
                    <div class="text-left">
                        <div class="mb-4">
                            <div class="text-2xl font-bold">John Doe</div>
                            <div class="text-lg italic">Software Engineer</div>
                            <div class="text-sm">john@example.com | (555) 123-4567 | New York, NY</div>
                        </div>
                        <div class="space-y-3">
                            <div>
                                <div class="text-sm font-bold border-b border-black inline-block">PROFESSIONAL SUMMARY</div>
                                <div class="text-sm">Experienced software engineer with expertise in...</div>
                            </div>
                            <div>
                                <div class="text-sm font-bold border-b border-black inline-block">SKILLS</div>
                                <div class="text-sm">JavaScript, Python, React, Node.js</div>
                            </div>
                        </div>
                    </div>
                `
            }
        };

        // Update template preview when selection changes
        templateSelect.addEventListener('change', function() {
            const selectedTemplate = templateStyles[this.value];
            templatePreview.innerHTML = `
                <div class="mb-2">
                    <h6 class="font-semibold text-gray-800">${selectedTemplate.name}</h6>
                    <p class="text-sm text-gray-600">${selectedTemplate.description}</p>
                </div>
                ${selectedTemplate.preview}
            `;
        });

        // Show initial preview
        templateSelect.dispatchEvent(new Event('change'));
    }

    // Generate resume
    document.getElementById('resume-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!isLoggedIn) {
            loginModal.style.display = 'block';
            return;
        }
        
        // Get elements with null checks
        const resumeLoader = document.getElementById('resume-loader');
        const resumeResult = document.getElementById('resume-result');
        
        // Show loader if it exists
        if (resumeLoader) {
            resumeLoader.classList.remove('hidden');
        }
        
        // Hide result if it exists
        if (resumeResult) {
            resumeResult.classList.add('hidden');
        }
        
        try {
            // Get form data
            const formData = new FormData(this);
            
            // Debug: Log all form data
            console.log('Form Data:', Object.fromEntries(formData));
            
            // Get selected format
            const selectedFormat = formData.get('format') || 'pdf';
            console.log('Selected resume format:', selectedFormat);
            
            // Get selected template
            const selectedTemplate = formData.get('template') || 'modern';
            console.log('Selected resume template:', selectedTemplate);
            
            // Check if user is a fresher 
            const isFresher = document.getElementById('isFresher')?.checked || false;
            
            // If user is a fresher, ensure experience fields aren't causing validation issues
            if (isFresher) {
                const experienceContainer = document.getElementById('experience-container');
                if (experienceContainer) {
                    const requiredInputs = experienceContainer.querySelectorAll('[required]');
                    requiredInputs.forEach(input => {
                        input.removeAttribute('required');
                    });
                }
            }
            
            // Collect experience data
            const experienceData = [];
            const experienceEntries = document.querySelectorAll('.experience-entry');
            console.log('Experience Entries:', experienceEntries.length);
            
            // Only collect experience data if the fresher checkbox is not checked
            if (!isFresher) {
                experienceEntries.forEach((entry, index) => {
                    const company = entry.querySelector(`[name="experience[${index}].company"]`)?.value;
                    const title = entry.querySelector(`[name="experience[${index}].title"]`)?.value;
                    const startDate = entry.querySelector(`[name="experience[${index}].startDate"]`)?.value;
                    const endDate = entry.querySelector(`[name="experience[${index}].endDate"]`)?.value;
                    const current = entry.querySelector(`[name="experience[${index}].current"]`)?.checked;
                    const description = entry.querySelector(`[name="experience[${index}].description"]`)?.value;
                    
                    console.log(`Experience ${index}:`, { company, title, startDate, endDate, current, description });
                    
                    if (company && title && startDate && description) {
                        experienceData.push({
                            company,
                            title,
                            startDate,
                            endDate: current ? null : endDate,
                            current,
                            description
                        });
                    }
                });
            }

            // Collect education data
            const educationData = [];
            const educationEntries = document.querySelectorAll('.education-entry');
            console.log('Education Entries:', educationEntries.length);
            
            educationEntries.forEach((entry, index) => {
                const institution = entry.querySelector(`[name="education[${index}].institution"]`)?.value;
                const degree = entry.querySelector(`[name="education[${index}].degree"]`)?.value;
                const field = entry.querySelector(`[name="education[${index}].field"]`)?.value;
                const graduationDate = entry.querySelector(`[name="education[${index}].graduationDate"]`)?.value;
                
                console.log(`Education ${index}:`, { institution, degree, field, graduationDate });
                
                if (institution && degree && graduationDate) {
                    educationData.push({
                        institution,
                        degree,
                        field,
                        graduationDate
                    });
                }
            });

            // Collect certification data
            const certificationData = [];
            const certificationEntries = document.querySelectorAll('.certification-entry');
            console.log('Certification Entries:', certificationEntries.length);
            
            certificationEntries.forEach((entry, index) => {
                const name = entry.querySelector(`[name="certifications[${index}].name"]`)?.value;
                const issuer = entry.querySelector(`[name="certifications[${index}].issuer"]`)?.value;
                
                console.log(`Certification ${index}:`, { name, issuer });
                
                if (name && issuer) {
                    certificationData.push({
                        name,
                        issuer
                    });
                }
            });

            // Collect project data
            const projectData = [];
            const projectEntries = document.querySelectorAll('.project-entry');
            projectEntries.forEach((entry, index) => {
                const name = entry.querySelector(`[name="project[${index}].name"]`)?.value;
                const technologies = entry.querySelector(`[name="project[${index}].technologies"]`)?.value;
                const startDate = entry.querySelector(`[name="project[${index}].startDate"]`)?.value;
                const endDate = entry.querySelector(`[name="project[${index}].endDate"]`)?.value;
                const current = entry.querySelector(`[name="project[${index}].current"]`)?.checked;
                const url = entry.querySelector(`[name="project[${index}].url"]`)?.value;
                const description = entry.querySelector(`[name="project[${index}].description"]`)?.value;
                
                if (name && technologies && startDate && description) {
                    projectData.push({
                        name,
                        description,
                        technologies: technologies.split(',').map(tech => tech.trim()),
                        startDate,
                        endDate: current ? null : endDate,
                        current,
                        url: url || null
                    });
                }
            });

            const resumeData = {
                personal_info: {
                    fullName: formData.get('fullName'),
                    title: formData.get('title'),
                    email: formData.get('email'),
                    phone: formData.get('phone'),
                    location: formData.get('location'),
                    linkedin: formData.get('linkedin'),
                    summary: formData.get('summary'),
                    skills: formData.get('skills').split(',').map(skill => skill.trim()),
                    experience: experienceData,
                    education: educationData,
                    certifications: certificationData,
                    projects: projectData
                },
                job_details: JSON.stringify({
                    job_title: window.lastAnalyzedJobDetails?.job_title || '',
                    description: window.lastAnalyzedJobDetails?.description || '',
                    company: window.lastAnalyzedJobDetails?.company || '',
                    location: window.lastAnalyzedJobDetails?.location || '',
                    reasoning: window.lastAnalyzedJobDetails?.reasoning || ''
                }),
                format: selectedFormat,
                template: selectedTemplate
            };

            // Debug: Log the final resume data
            console.log('Final Resume Data:', JSON.stringify(resumeData, null, 2));
            
            // Check if we have a job ID from a previous analysis
            if (!window.lastAnalyzedJobId) {
                throw new Error('No job ID found. Please analyze a job posting first before generating a resume.');
            }
            
            // Debug the job ID
            console.log('Using job ID for resume generation:', window.lastAnalyzedJobId);
            
            // Create URL with job_id parameter
            const url = `${API_ENDPOINTS.generateResume}?job_id=${window.lastAnalyzedJobId}`;
            console.log('Resume generation URL:', url);
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `${tokenType} ${authToken}`
                },
                body: JSON.stringify(resumeData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail)) {
                        throw new Error(errorData.detail.map(err => err.msg).join(', '));
                    } else {
                        throw new Error(errorData.detail);
                    }
                }
                throw new Error('Failed to generate resume');
            }
            
            const result = await response.json();
            
            // Show success message if result element exists
            if (resumeResult) {
                resumeResult.classList.remove('hidden');
                resumeResult.innerHTML = `
                    <div class="p-4 rounded-lg bg-green-50">
                        <div class="flex items-center">
                            <i class="bi bi-check-circle-fill text-green-500 mr-2"></i>
                            <h3 class="text-lg font-semibold text-green-700">Resume Generated Successfully</h3>
                        </div>
                        <p class="mt-2 text-green-600">Your resume has been generated and saved. You can view it in your history.</p>
                    </div>
                `;
            }
            
            // Use the improved download function
            await downloadResume(result.id, selectedFormat);
            
            // Removed form reset to preserve form data
            // this.reset();
            
        } catch (error) {
            console.error('Error generating resume:', error);
            // Show error message if result element exists
            if (resumeResult) {
                resumeResult.classList.remove('hidden');
                resumeResult.innerHTML = `
                    <div class="p-4 rounded-lg bg-red-50">
                        <div class="flex items-center">
                            <i class="bi bi-exclamation-triangle-fill text-red-500 mr-2"></i>
                            <h3 class="text-lg font-semibold text-red-700">Error Generating Resume</h3>
                        </div>
                        <p class="mt-2 text-red-600">${error.message}</p>
                    </div>
                `;
            }
        } finally {
            // Hide loader if it exists
            if (resumeLoader) {
                resumeLoader.classList.add('hidden');
            }
        }
    });

    // PDF Upload handling
    const resumeUpload = document.getElementById('resume-upload');
    const uploadStatus = document.getElementById('upload-status');
    const parseError = document.getElementById('parse-error');

    resumeUpload.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        if (!file.type.includes('pdf')) {
            parseError.textContent = 'Please upload a PDF file';
            parseError.classList.remove('hidden');
            parseError.classList.remove('text-green-600');
            parseError.classList.add('text-red-600');
            return;
        }
        
        // Show upload status
        uploadStatus.classList.remove('hidden');
        parseError.classList.add('hidden');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(API_ENDPOINTS.parsePdf, {
                method: 'POST',
                headers: {
                    'Authorization': `${tokenType} ${authToken}`
                },
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to parse PDF');
            }
            
            const parsedData = await response.json();
            console.log('PDF Parsed Data:', parsedData);
            
            // Check if the profile is a fresher
            const isFresher = parsedData.isFresher || false;
            const fresherCheckbox = document.getElementById('isFresher');
            
            // Set the fresher checkbox if available and indicated in the parsed data
            if (fresherCheckbox && isFresher) {
                console.log('Setting fresher checkbox to checked');
                fresherCheckbox.checked = true;
                
                // Trigger the change event to show/hide relevant sections
                const changeEvent = new Event('change');
                fresherCheckbox.dispatchEvent(changeEvent);
            }
            
            // Populate form with parsed data
            populateFormWithData(parsedData);
            
            // Hide status and show success message
            uploadStatus.classList.add('hidden');
            parseError.textContent = 'Resume parsed successfully!';
            parseError.classList.remove('hidden');
            parseError.classList.remove('text-red-600');
            parseError.classList.add('text-green-600');
            
        } catch (error) {
            console.error('Error parsing PDF:', error);
            uploadStatus.classList.add('hidden');
            parseError.textContent = 'Error parsing PDF. Please try again or fill the form manually.';
            parseError.classList.remove('hidden');
            parseError.classList.remove('text-green-600');
            parseError.classList.add('text-red-600');
        }
    });

    function populateFormWithData(data) {
        // Basic info
        const fullNameEl = document.getElementById('fullName');
        if (fullNameEl) fullNameEl.value = data.fullName || '';
        
        const titleEl = document.getElementById('title');
        if (titleEl) titleEl.value = data.title || '';
        
        const emailEl = document.getElementById('email');
        if (emailEl) emailEl.value = data.email || '';
        
        const phoneEl = document.getElementById('phone');
        if (phoneEl) phoneEl.value = data.phone || '';
        
        const locationEl = document.getElementById('location');
        if (locationEl) locationEl.value = data.location || '';
        
        const linkedinEl = document.getElementById('linkedin');
        if (linkedinEl) linkedinEl.value = data.linkedin || '';
        
        // Skills - join array with commas
        if (data.skills && data.skills.length > 0) {
            const skillsEl = document.getElementById('skills');
            if (skillsEl) skillsEl.value = data.skills.join(', ');
        }
        
        // Check if the profile is a fresher
        const isFresher = data.isFresher || false;
        const fresherCheckbox = document.getElementById('isFresher');
        const experienceSection = document.getElementById('experience-section');
        
        // Set the fresher checkbox if indicated in the parsed data
        if (fresherCheckbox && isFresher) {
            console.log('Setting fresher checkbox to checked in populateFormWithData');
            fresherCheckbox.checked = true;
            
            // Hide experience section
            if (experienceSection) {
                experienceSection.classList.add('hidden');
            }
            
            // Remove required attribute from experience fields
        const experienceContainer = document.getElementById('experience-container');
        if (experienceContainer) {
                const requiredInputs = experienceContainer.querySelectorAll('[required]');
                requiredInputs.forEach(input => {
                    input.removeAttribute('required');
                });
                
                // Explicitly check for textarea to ensure it's not required
                const textareas = experienceContainer.querySelectorAll('textarea');
                textareas.forEach(textarea => {
                    textarea.removeAttribute('required');
                });
            }
        } else {
            // Make sure experience section is visible if not a fresher
            if (experienceSection) {
                experienceSection.classList.remove('hidden');
            }
        }
        
        // Experience - Only populate if not a fresher
        const experienceContainer = document.getElementById('experience-container');
        if (experienceContainer && data.experience && data.experience.length > 0 && !isFresher) {
            // Clear existing experience entries except the first one
            const entries = experienceContainer.querySelectorAll('.experience-entry');
            for (let i = 1; i < entries.length; i++) {
                entries[i].remove();
            }
            
            // Process each experience entry
            data.experience.forEach((exp, index) => {
                // If index is 0, update the existing first entry
                if (index === 0) {
                    const firstEntry = experienceContainer.querySelector('.experience-entry');
                    if (firstEntry) {
                        firstEntry.querySelector(`[name="experience[0].company"]`).value = exp.company || '';
                        firstEntry.querySelector(`[name="experience[0].title"]`).value = exp.title || '';
                        firstEntry.querySelector(`[name="experience[0].startDate"]`).value = exp.startDate || '';
                        firstEntry.querySelector(`[name="experience[0].endDate"]`).value = exp.endDate || '';
                        
                        const currentCheckbox = firstEntry.querySelector(`[name="experience[0].current"]`);
                        if (currentCheckbox) {
                            currentCheckbox.checked = exp.current || false;
                        }
                        
                        const desc = firstEntry.querySelector(`[name="experience[0].description"]`);
                        if (desc) {
                            desc.value = exp.description || '';
                        }
                    }
                }
                // For additional entries, create new ones
                else {
                    // Trigger the add experience button click to create a new entry
                    const addButton = document.getElementById('add-experience');
                    if (addButton) {
                        addButton.click();
                        
                        // Now populate the newly created entry
                        const newEntry = experienceContainer.querySelectorAll('.experience-entry')[index];
                        if (newEntry) {
                            newEntry.querySelector(`[name="experience[${index}].company"]`).value = exp.company || '';
                            newEntry.querySelector(`[name="experience[${index}].title"]`).value = exp.title || '';
                            newEntry.querySelector(`[name="experience[${index}].startDate"]`).value = exp.startDate || '';
                            newEntry.querySelector(`[name="experience[${index}].endDate"]`).value = exp.endDate || '';
                            
                            const currentCheckbox = newEntry.querySelector(`[name="experience[${index}].current"]`);
                            if (currentCheckbox) {
                                currentCheckbox.checked = exp.current || false;
                            }
                            
                            const desc = newEntry.querySelector(`[name="experience[${index}].description"]`);
                            if (desc) {
                                desc.value = exp.description || '';
                            }
                        }
                    }
                }
            });
        }

        // Education - same structure as before
        const educationContainer = document.getElementById('education-container');
        if (educationContainer) {
            // ... existing education population code ...
        }

        // Certification - same structure as before
        const certificationContainer = document.getElementById('certification-container');
        if (certificationContainer) {
            // ... existing certification population code ...
        }
        
        // Projects - NEW section for populating projects data
        const projectsContainer = document.getElementById('projects-container');
        if (projectsContainer) {
            projectsContainer.innerHTML = ''; // Clear existing projects
            
            // Create default empty project entry if no projects data
            if (!data.projects || data.projects.length === 0) {
                const entry = document.createElement('div');
                entry.className = 'project-entry space-y-4 pb-4 border-b border-gray-200';
                
                entry.innerHTML = `
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label for="project-0-name" class="block text-sm font-medium text-gray-700 mb-1">Project Name <span class="text-red-500">*</span></label>
                            <input type="text" id="project-0-name" name="project[0].name" required 
                                class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                        </div>
                        <div>
                            <label for="project-0-technologies" class="block text-sm font-medium text-gray-700 mb-1">Technologies Used <span class="text-red-500">*</span></label>
                            <input type="text" id="project-0-technologies" name="project[0].technologies" required 
                                class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="Comma-separated list of technologies">
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label for="project-0-startDate" class="block text-sm font-medium text-gray-700 mb-1">Start Date <span class="text-red-500">*</span></label>
                            <input type="text" id="project-0-startDate" name="project[0].startDate" required 
                                class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="MM/YYYY">
                        </div>
                        <div>
                            <label for="project-0-endDate" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                            <input type="text" id="project-0-endDate" name="project[0].endDate" 
                                class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="MM/YYYY or leave empty if ongoing">
                        </div>
                    </div>
                    <div>
                        <label for="project-0-url" class="block text-sm font-medium text-gray-700 mb-1">Project URL (Optional)</label>
                        <input type="url" id="project-0-url" name="project[0].url" 
                            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            placeholder="https://github.com/username/project">
                    </div>
                    <div>
                        <label for="project-0-description" class="block text-sm font-medium text-gray-700 mb-1">Project Description <span class="text-red-500">*</span></label>
                        <textarea id="project-0-description" name="project[0].description" required rows="3"
                            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            placeholder="Describe the project, your role, and key achievements"></textarea>
                    </div>
                    <div class="flex items-center">
                        <input type="checkbox" id="project-0-current" name="project[0].current" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
                        <label for="project-0-current" class="ml-2 block text-sm text-gray-700">This is an ongoing project</label>
                    </div>
                `;
                
                projectsContainer.appendChild(entry);
            } else {
                // Populate projects data
                data.projects.forEach((project, index) => {
                    const entry = document.createElement('div');
                    entry.className = 'project-entry space-y-4 pb-4 border-b border-gray-200';
                    
                    // Create HTML structure
                    entry.innerHTML = `
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label for="project-${index}-name" class="block text-sm font-medium text-gray-700 mb-1">Project Name <span class="text-red-500">*</span></label>
                                <input type="text" id="project-${index}-name" name="project[${index}].name" required 
                                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                            </div>
                            <div>
                                <label for="project-${index}-technologies" class="block text-sm font-medium text-gray-700 mb-1">Technologies Used <span class="text-red-500">*</span></label>
                                <input type="text" id="project-${index}-technologies" name="project[${index}].technologies" required 
                                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    placeholder="Comma-separated list of technologies">
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label for="project-${index}-startDate" class="block text-sm font-medium text-gray-700 mb-1">Start Date <span class="text-red-500">*</span></label>
                                <input type="text" id="project-${index}-startDate" name="project[${index}].startDate" required 
                                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    placeholder="MM/YYYY">
                            </div>
                            <div>
                                <label for="project-${index}-endDate" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                                <input type="text" id="project-${index}-endDate" name="project[${index}].endDate" 
                                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    placeholder="MM/YYYY or leave empty if ongoing">
                            </div>
                        </div>
                        <div>
                            <label for="project-${index}-url" class="block text-sm font-medium text-gray-700 mb-1">Project URL (Optional)</label>
                            <input type="url" id="project-${index}-url" name="project[${index}].url" 
                                class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="https://github.com/username/project">
                        </div>
                        <div>
                            <label for="project-${index}-description" class="block text-sm font-medium text-gray-700 mb-1">Project Description <span class="text-red-500">*</span></label>
                            <textarea id="project-${index}-description" name="project[${index}].description" required rows="3"
                                class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="Describe the project, your role, and key achievements"></textarea>
                        </div>
                        <div class="flex items-center">
                            <input type="checkbox" id="project-${index}-current" name="project[${index}].current" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
                            <label for="project-${index}-current" class="ml-2 block text-sm text-gray-700">This is an ongoing project</label>
                        </div>
                    `;
                    
                    // Set values from project data
                    entry.querySelector(`[name="project[${index}].name"]`).value = project.name || '';
                    
                    // Handle technologies as array or string
                    const techValue = Array.isArray(project.technologies) 
                        ? project.technologies.join(', ') 
                        : (project.technologies || '');
                    entry.querySelector(`[name="project[${index}].technologies"]`).value = techValue;
                    
                    entry.querySelector(`[name="project[${index}].startDate"]`).value = project.startDate || '';
                    entry.querySelector(`[name="project[${index}].endDate"]`).value = project.endDate || '';
                    entry.querySelector(`[name="project[${index}].url"]`).value = project.url || '';
                    entry.querySelector(`[name="project[${index}].description"]`).value = project.description || '';
                    entry.querySelector(`[name="project[${index}].current"]`).checked = project.current || false;
                    
                    // Add remove button for projects after the first one
                    if (index > 0) {
                        const removeBtn = document.createElement('button');
                        removeBtn.type = 'button';
                        removeBtn.className = 'remove-project text-red-600 hover:text-red-700 text-sm font-medium mt-2 flex items-center focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1';
                        removeBtn.innerHTML = `
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                            Remove Project
                        `;
                        removeBtn.addEventListener('click', function() {
                            entry.remove();
                        });
                        entry.appendChild(removeBtn);
                    }
                    
                    projectsContainer.appendChild(entry);
                });
            }
        }
    }

    // Add project entry
    document.getElementById('add-project')?.addEventListener('click', function() {
        const container = document.getElementById('projects-container');
        if (!container) return; // Make sure container exists
        
        const entries = container.querySelectorAll('.project-entry');
        const newIndex = entries.length;
        
        const newEntry = document.createElement('div');
        newEntry.className = 'project-entry space-y-4 pb-4 border-b border-gray-200';
        newEntry.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label for="project-${newIndex}-name" class="block text-sm font-medium text-gray-700 mb-1">Project Name <span class="text-red-500">*</span></label>
                    <input type="text" id="project-${newIndex}-name" name="project[${newIndex}].name" required 
                        class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                </div>
                <div>
                    <label for="project-${newIndex}-technologies" class="block text-sm font-medium text-gray-700 mb-1">Technologies Used <span class="text-red-500">*</span></label>
                    <input type="text" id="project-${newIndex}-technologies" name="project[${newIndex}].technologies" required 
                        class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        placeholder="Comma-separated list of technologies">
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label for="project-${newIndex}-startDate" class="block text-sm font-medium text-gray-700 mb-1">Start Date <span class="text-red-500">*</span></label>
                    <input type="text" id="project-${newIndex}-startDate" name="project[${newIndex}].startDate" required 
                        class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        placeholder="MM/YYYY">
                </div>
                <div>
                    <label for="project-${newIndex}-endDate" class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input type="text" id="project-${newIndex}-endDate" name="project[${newIndex}].endDate" 
                        class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        placeholder="MM/YYYY or leave empty if ongoing">
                </div>
            </div>
            <div>
                <label for="project-${newIndex}-url" class="block text-sm font-medium text-gray-700 mb-1">Project URL (Optional)</label>
                <input type="url" id="project-${newIndex}-url" name="project[${newIndex}].url" 
                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    placeholder="https://github.com/username/project">
            </div>
            <div>
                <label for="project-${newIndex}-description" class="block text-sm font-medium text-gray-700 mb-1">Project Description <span class="text-red-500">*</span></label>
                <textarea id="project-${newIndex}-description" name="project[${newIndex}].description" required rows="3"
                    class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    placeholder="Describe the project, your role, and key achievements"></textarea>
            </div>
            <div class="flex items-center">
                <input type="checkbox" id="project-${newIndex}-current" name="project[${newIndex}].current" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
                <label for="project-${newIndex}-current" class="ml-2 block text-sm text-gray-700">This is an ongoing project</label>
            </div>
        `;
        
        // Add a remove button if it's not the first entry
        if (newIndex > 0) {
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-project text-red-600 hover:text-red-700 text-sm font-medium mt-2 flex items-center focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1';
            removeBtn.innerHTML = `
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
                Remove Project
            `;
            removeBtn.addEventListener('click', function() {
                newEntry.remove();
            });
            newEntry.appendChild(removeBtn);
        }
        
        container.appendChild(newEntry);
    });

    // Add event listeners for existing remove buttons
    document.querySelectorAll('.remove-project').forEach(button => {
        button.addEventListener('click', function() {
            const entry = this.closest('.project-entry');
            if (entry && entry.parentNode) {
                entry.parentNode.removeChild(entry);
            }
        });
    });

    async function deleteJobAnalysis(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `${tokenType} ${authToken}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete job analysis');
            }

            // Remove the job card from the UI
            const jobCard = document.querySelector(`.delete-job-btn[data-id="${jobId}"]`)?.closest('.bg-white');
            if (jobCard) {
                jobCard.remove();
                
                // Check if there are any remaining job cards
                const remainingJobs = document.querySelectorAll('#job-history-list .bg-white');
                if (remainingJobs.length === 0) {
                    jobHistoryList.innerHTML = '<p class="text-center text-gray-500">No job analyses found</p>';
                }
            }

            showNotification('Job analysis deleted successfully', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    async function deleteResume(resumeId) {
        try {
            const response = await fetch(`${API_BASE_URL}/resumes/${resumeId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete resume');
            }

            showNotification('Resume deleted successfully', 'success');
            loadResumeHistory(); // Refresh the history
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    // Improved function for downloading resumes with proper content type handling
    async function downloadResume(resumeId, format = 'pdf') {
        try {
            const downloadUrl = `${API_ENDPOINTS.downloadResume}/${resumeId}`;
            
            // Show a loading notification
            showNotification('Preparing resume for download...', 'success');
            
            // Add a small delay (2 seconds) to allow the server time to generate the file
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            console.log('Attempting to download resume from:', downloadUrl);
            const downloadResponse = await fetch(downloadUrl, {
                method: 'GET',
                headers: {
                    'Authorization': `${tokenType} ${authToken}`
                }
            });

            if (!downloadResponse.ok) {
                let errorText = 'Unknown error';
                try {
                    const errorData = await downloadResponse.json();
                    errorText = errorData.detail || `HTTP ${downloadResponse.status}`;
                } catch (e) {
                    errorText = `HTTP ${downloadResponse.status}: ${downloadResponse.statusText}`;
                }
                throw new Error(`Failed to download resume: ${errorText}`);
            }

            // Get content type from response
            const contentType = downloadResponse.headers.get('Content-Type');
            console.log('Resume download content type:', contentType);
            
            // Get filename from Content-Disposition header if available, otherwise create one
            const disposition = downloadResponse.headers.get('Content-Disposition');
            let filename = `resume_${resumeId}.${format.toLowerCase()}`; // Default filename with appropriate extension
            
            if (disposition && disposition.includes('filename=')) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            // Get the response as a blob with the correct type
            let blobType = 'application/octet-stream'; // Default fallback
            if (contentType) {
                blobType = contentType;
            } else if (format.toLowerCase() === 'pdf') {
                blobType = 'application/pdf';
            } else if (format.toLowerCase() === 'docx') {
                blobType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
            }
            
            const blob = await downloadResponse.blob();
            // Create a new blob with the correct content type
            const fileBlob = new Blob([blob], { type: blobType });
            
            // Create and trigger download
            const url = window.URL.createObjectURL(fileBlob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('Resume downloaded successfully!', 'success');
            return true;
        } catch (error) {
            console.error('Error downloading resume:', error);
            showNotification(`Error downloading resume: ${error.message}`, 'error');
            return false;
        }
    }
});