# BYS360 CIC V3.0 Mail Engine System Sender V1.1

Bu paket, service dosyasında birden fazla `send_task` tanımı bulunması durumunda regex ile tekil değiştirme yapmaz. Bunun yerine dosya sonuna kararlı `send_task` bloğu ekler ve Python'un son fonksiyon tanımı kuralıyla mail gönderim motorunu sistem MAIL/SMTP ayarlarını kullanacak şekilde güvenli biçimde ezer.
