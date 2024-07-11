// // login.html
// function validateForm(event) {
//         event.preventDefault();
//         var recaptchaResponse = grecaptcha.getResponse();
//         if (recaptchaResponse.length === 0) {
//             document.getElementById('recaptcha-error').style.display = 'block';
//         } else {
//             document.getElementById('recaptcha-error').style.display = 'none';
//             window.location.href = 'otp.html';
//         }
//     }

// index.html
document.addEventListener("DOMContentLoaded", () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    }, {
        threshold: 0.5 
    });

    document.querySelectorAll('.fade-in-section').forEach((section) => {
        observer.observe(section);
    });
    const featureContainers = document.querySelectorAll('.feature-container');

    featureContainers.forEach(container => {
        container.addEventListener('click', () => {
            const description = container.querySelector('.feature-description');
            description.style.opacity = description.style.opacity === '0' ? '1' : '0';
        });
    });
});

