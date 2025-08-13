const form = document.getElementById('form')
const firstname_input = document.getElementById('firstname-input')
const email_input = document.getElementById('email-input')
const password_input = document.getElementById('password-input')
const repeat_password_input = document.getElementById('repeat-password-input')
const error_message = document.getElementById('error-message')

form.addEventListener('submit', (e) => {
    e.preventDefault(); // always prevent default form submit

    let errors = [];

    if(firstname_input) {
        errors = getSignupFormErrors(firstname_input.value, email_input.value, password_input.value, repeat_password_input.value)
    }
    else {
        errors = getLoginFormErrors(email_input.value, password_input.value)
    }

    if(errors.length > 0) {
        error_message.innerText = errors.join(". ")
        return; // stop if errors
    }

    // No errors: send POST to backend
    // Determine if this is login or signup based on presence of firstname field
    const isSignup = firstname_input !== null;
    const endpoint = isSignup ? '/auth/signup' : '/auth/login';
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    
    let requestBody;
    if (isSignup) {
        requestBody = {
            first_name: firstname_input.value,
            email: email_input.value,
            password: password_input.value
        };
    } else {
        requestBody = {
            email: email_input.value,
            password: password_input.value
        };
    }
    
    const headers = { 'Content-Type': 'application/json' };
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    fetch(endpoint, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestBody)
    })
    .then(res => res.json())
    .then(data => {
        if(data.message) {
            error_message.style.color = 'green';
            error_message.innerText = data.message;
            
            // Replace parent window with dashboard (closes popup)
            setTimeout(() => {
                if (window.parent && window.parent !== window) {
                    // If this is an iframe, communicate with parent
                    window.parent.postMessage({action: 'redirect', url: '/dashboard'}, '*');
                } else {
                    // If not in iframe, redirect normally
                    window.location.replace('/dashboard');
                }
            }, 1500); // 1.5 second delay to show success message
        } else if(data.error) {
            error_message.style.color = 'red';
            error_message.innerText = data.error;
        }
    })
    .catch(err => {
        error_message.style.color = 'red';
        error_message.innerText = 'Server or network error.';
        console.error(err);
    });
});

function getSignupFormErrors(firstname, email, password, repeatpassword) {
    let errors = []

    if(firstname == '' || firstname == null) {
        errors.push('Firstname is required')
        firstname_input.parentElement.classList.add('incorrect')
    }
    if(email == '' || email == null) {
        errors.push('Email is required')
        email_input.parentElement.classList.add('incorrect')
    }
    if(password == '' || password == null) {
        errors.push('Password is required')
        password_input.parentElement.classList.add('incorrect')
    }
    if (password.length > 0 && password.length < 8 ) {
        errors.push('Password must have at least 8 characters')
        password_input.parentElement.classList.add('incorrect')
    }

    if(password !== repeatpassword) {
        errors.push('Passwords do not match')
        password_input.parentElement.classList.add('incorrect')
        repeat_password_input.parentElement.classList.add('incorrect')
    }

    return errors;
}

function getLoginFormErrors (email, password) {
    let errors = []

    if(email == '' || email == null) {
        errors.push('Email is required')
        email_input.parentElement.classList.add('incorrect')
    }
    if(password == '' || password == null) {
        errors.push('Password is required')
        password_input.parentElement.classList.add('incorrect')
    }

    return errors;
}

const allInputs = [firstname_input, email_input, password_input, repeat_password_input].filter(input => input != null)

allInputs.forEach(input => {
    input.addEventListener('input', () => {
        if (input.parentElement.classList.contains('incorrect')) {
            input.parentElement.classList.remove('incorrect')
            error_message.innerText = ''
        }
    })
})