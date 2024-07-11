function validateForm(event) {
        event.preventDefault();
        var recaptchaResponse = grecaptcha.getResponse();
        if (recaptchaResponse.length === 0) {
            document.getElementById('recaptcha-error').style.display = 'block';
        } else {
            document.getElementById('recaptcha-error').style.display = 'none';
            showOTPForm(event);
        }
    }