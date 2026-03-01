/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./templates/**/*.html"],
    safelist: [
        {
            pattern: /bg-(neon-cyan|neon-pink|neon-green|neon-purple|neon-amber|neon-red|neon-blue)/,
            variants: ['hover', 'group-hover'],
        },
        {
            pattern: /text-(neon-cyan|neon-pink|neon-green|neon-purple|neon-amber|neon-red|neon-blue)/,
            variants: ['hover', 'group-hover'],
        },
        {
            pattern: /border-(neon-cyan|neon-pink|neon-green|neon-purple|neon-amber|neon-red|neon-blue)/,
            variants: ['hover', 'group-hover'],
        },
        {
            pattern: /(bg|text|border)-(neon-cyan|neon-pink|neon-green|neon-purple|neon-amber|neon-red|neon-blue)\/(10|20|30|40|50|60|70|80)/,
            variants: ['hover', 'group-hover'],
        },
    ],
    theme: {
        extend: {
            colors: {
                'void': '#0a0a0f',
                'void-dark': '#050508',
                'void-light': '#12121a',
                'void-lighter': '#1a1a25',
                'neon-cyan': '#00f5ff',
                'neon-pink': '#ff00ff',
                'neon-green': '#00ff88',
                'neon-amber': '#ffaa00',
                'neon-red': '#ff3355',
                'neon-purple': '#bd00ff',
                'neon-blue': '#2979ff',
            },
            fontFamily: {
                'display': ['"Clash Display"', 'system-ui', 'sans-serif'],
                'mono': ['"JetBrains Mono"', 'monospace'],
            },
            animation: {
                'glow': 'glow 2s ease-in-out infinite alternate',
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 3s ease-in-out infinite',
                'scan': 'scan 2s ease-in-out infinite',
            },
        },
    },
    plugins: [],
}
