/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
  	extend: {
  		fontFamily: {
  			sans: ['Inter', 'sans-serif'],
  			document: ['"Public Sans"', 'sans-serif'],
  		},
  		colors: {
  			background: "var(--background)",
  			surface: "var(--surface)",
  			'surface-dim': "var(--surface-dim)",
  			'surface-bright': "var(--surface-bright)",
  			'surface-container-lowest': "var(--surface-container-lowest)",
  			'surface-container-low': "var(--surface-container-low)",
  			'surface-container': "var(--surface-container)",
  			'surface-container-high': "var(--surface-container-high)",
  			'surface-container-highest': "var(--surface-container-highest)",
  			'surface-variant': "var(--surface-variant)",
  			
  			'on-background': "var(--on-background)",
  			'on-surface': "var(--on-surface)",
  			'on-surface-variant': "var(--on-surface-variant)",

  			primary: {
  				DEFAULT: "var(--primary)",
  				container: "var(--primary-container)",
  				fixed: "var(--primary-fixed)",
  				'fixed-dim': "var(--primary-fixed-dim)",
  			},
  			'on-primary': "var(--on-primary)",
  			'on-primary-container': "var(--on-primary-container)",
  			'on-primary-fixed': "var(--on-primary-fixed)",
  			'on-primary-fixed-variant': "var(--on-primary-fixed-variant)",

  			secondary: {
  				DEFAULT: "var(--secondary)",
  				container: "var(--secondary-container)",
  				fixed: "var(--secondary-fixed)",
  				'fixed-dim': "var(--secondary-fixed-dim)",
  			},
  			'on-secondary': "var(--on-secondary)",
  			'on-secondary-container': "var(--on-secondary-container)",
  			'on-secondary-fixed': "var(--on-secondary-fixed)",
  			'on-secondary-fixed-variant': "var(--on-secondary-fixed-variant)",

  			tertiary: {
  				DEFAULT: "var(--tertiary)",
  				container: "var(--tertiary-container)",
  				fixed: "var(--tertiary-fixed)",
  				'fixed-dim': "var(--tertiary-fixed-dim)",
  			},
  			'on-tertiary': "var(--on-tertiary)",
  			'on-tertiary-container': "var(--on-tertiary-container)",
  			'on-tertiary-fixed': "var(--on-tertiary-fixed)",
  			'on-tertiary-fixed-variant': "var(--on-tertiary-fixed-variant)",

  			error: {
  				DEFAULT: "var(--error)",
  				container: "var(--error-container)",
  			},
  			'on-error': "var(--on-error)",
  			'on-error-container': "var(--on-error-container)",

  			outline: {
  				DEFAULT: "var(--outline)",
  				variant: "var(--outline-variant)",
  			},
  			
  			inverse: {
  				surface: "var(--inverse-surface)",
  				'on-surface': "var(--inverse-on-surface)",
  				primary: "var(--inverse-primary)",
  			}
  		},
  		boxShadow: {
  			'ambient': '0px 10px 30px rgba(9, 20, 38, 0.06)',
  			'ambient-dark': '0px 10px 30px rgba(0, 0, 0, 0.25)',
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
