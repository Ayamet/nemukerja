from nemukerja.app import create_app

# Membuat instance aplikasi menggunakan factory 'create_app'
app = create_app()

# Menjalankan aplikasi
if __name__ == '__main__':
    # Anda bisa mengatur host dan port di sini jika perlu
    # contoh: app.run(host='0.0.0.0', port=8000, debug=True)
    app.run(debug=True)
