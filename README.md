# Kick Chronicle 
**Platform Highlight& Jadwal Sepak Bola"
Kick Chronicle meruapakn sebuah aplikasi web yang menyajikan video highlight pertandingan sepak bola, statistik tim, serta penjadwalan yang dapat terhubung dengan Google Calendar. Aplikasi web ini mendukung autentikasi autentikasi Google OAuth.


## Deskripsi Aplikasi
### Ringkasan Aplikasi
Tujuan : Memudahkan para penggemar sepak bola untuk mengakses video highlight, memantau statistik, dan mengelola jadwal pertandingan favorit dalam satu platform yang utuh.

Masalah yang dipecahkan: semua informasi penting yang dibutuhkan oleh para penggemar dapat diakses dalam satu platform.

### Fungsi Utama
Aplikasi ini menyediakan video highlight pertandingan sepak bola, statistik tim, penjadwalan pertandingan yang dapat disinkronkan ke Google Calendar, Login dan Autentikasi Google OAuth, Fitur interaktif (Like, Komen, dan Rating), dan pencarian filter.

### Target Pengguna
Penggemar olahraga sepak bola

## Fitur Utama
### User
- Autentikasi dengan Google OAuth
- Menonton highlight pertandingan
- Memperoleh statistik dan klasemen tim
- Menambahkan jadwal pertandingan Google Calendar yang berupa export file .ics
- User dapat berkomentar, memberi like dan komen sesuai dengan video highlight yang diinginkan

### Admin
- Admin dapat mengimplementasi CRUD data tim, jadwal, dan highlight
- Impor dan Ekspor dataset 
- Menjadi mod pada sesi komentar (mencegah komentar buruk)

## Daftar Modul 
- Auth & Profil -> Login, Registrasi, Google OAuth, profil pengguna (Alternatif -> tidak menggunakan Google Oauth dan implementasi dasar login register saja)
- Highlight -> Daftar dan detail highlight serta pencarian
- Tim -> Daftar tim dan klasemen
- Komentar, Like, Rating -> Reaction pada video highlight yang ditonton
- Panel Admin -> CRUD data dan impor atau ekspor dataset
- Kalender -> Integrasi jadwal dalam bentuk file yang dapat di import ke google calender (Alternatif -> Atur jadwal hanya bisa dilakukan pada web setelah user melakukan login)

## Initial Dataset
- Highlight diambil dari embded video yang ada di Youtube
-  Dataset sepak bola berbentuk CSV/JSON :
https://github.com/openfootball

https://www.kaggle.com/search?q=football+dataset

## Tautan Deployment PWS dan Link Design
- PWS : derrick-kickchronicle.pbp.cs.ui.ac.id
- Figma : https://www.figma.com/design/IoJuqP32KoKrtjMn1QZBU2/Web-PBP?node-id=0-1&t=wWxrSbKCbXsgsOid-1
