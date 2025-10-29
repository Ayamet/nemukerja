function togglePassword(id) {
    var pwd = document.getElementById(id);
    var eye = document.getElementById('eye-' + id);
    if (pwd.type === 'password') {
        pwd.type = 'text';
        eye.classList.remove('fa-eye');
        eye.classList.add('fa-eye-slash');
    } else {
        pwd.type = 'password';
        eye.classList.add('fa-eye');
        eye.classList.remove('fa-eye-slash');
    }
}

function enableSignUp() {
    document.getElementById("signup_btn").disabled = false;
}

