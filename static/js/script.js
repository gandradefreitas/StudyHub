const elementos = document.querySelectorAll(".oculto");

const observer = new IntersectionObserver((entries) => {

    entries.forEach((entry) => {

        if (entry.isIntersecting) {

            entry.target.classList.add("visivel");

        }

    });

});

elementos.forEach((elemento) => observer.observe(elemento));