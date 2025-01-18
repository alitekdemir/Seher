# 🌙 **Seher - Namaz Vakitleri Masaüstü Uygulaması**

**Seher**, Türkiye’nin herhangi bir iline veya ilçesine göre namaz vakitlerini anlık olarak takip etmenizi sağlayan masaüstü bir uygulamadır. Hafif, modern ve kullanıcı dostu bir arayüze sahiptir. 

***

## 📋 **Özellikler**

✅ **Güncel namaz vakitleri**: Diyanet İşleri Başkanlığı’ndan alınan doğru ve güvenilir bilgiler.  
✅ **Yatay ve dikey görünüm**: Ekranınıza en uygun tasarımı seçin.  
✅ **Kritik vakit uyarıları**: Renk değişimleriyle yaklaşan vakitleri gözden kaçırmayın.  
✅ **Kişiselleştirilebilir**: Renkler, yazı tipi, konum ve uyarı sürelerini kolayca düzenleyin.  
✅ **Kurulum gerekmez**: İndir, tıkla, çalıştır!  

### 🎥 Ekran Görüntüleri

|                                       Yatay Görünüm                                       |                                       Dikey Görünüm                                       |                                       İkaz Görünümü                                       |
| :---------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------: |
| ![image](https://github.com/user-attachments/assets/e119c046-c844-4b53-b51c-144a953081cd) | ![image](https://github.com/user-attachments/assets/e3067f53-4f1c-49c8-82be-b58f07713828) | ![image](https://github.com/user-attachments/assets/1f34d873-2bc4-4c59-a453-3961606a02b2) |


#### Ayarlar Ekranı:
![Seher_20250118-155323](https://github.com/user-attachments/assets/ee209a87-408d-4700-a7bf-8cd7e2a9d4dc)


***

## 🚀 **Kurulum ve Kullanım**

### **Nasıl İndirilir?**
1. GitHub’daki **[Releases](https://github.com/alitekdemir/Seher/releases)** sayfasını ziyaret edin.
2. En son sürümü seçip `Seher.exe` dosyasını indirin.
3. İndirdiğiniz dosyayı çift tıklayarak çalıştırın. Uygulama otomatik olarak başlatılacaktır.

### **Konum ve Namaz Vakitlerini Ayarlama**
1. **Ayarlar** penceresini açmak için widget üzerine **çift tıklayın**.
2. İl plaka kodunu girin ve ilçeleri listelemek için **"İlçeleri Getir"** butonuna tıklayın.
3. İlçenizi seçip **"Kaydet"** butonuna tıklayın.
4. **"Vakitleri Güncelle"** butonuyla namaz vakitlerinizi otomatik olarak alın.

### **Widget’ın Taşınması**
- Pencerenizi sürüklemek için **sol tık** kullanarak istediğiniz yere taşıyabilirsiniz.
- Uygulama ekranın kenarlarına yakın konumlandırıldığında otomatik olarak hizalanır.

***

## 📚 **Sistem Gereksinimleri**

**Desteklenen İşletim Sistemleri**:  
- Windows 7, 8, 10, 11

**Gereksinimler**:  
- Uygulama tamamen bağımsız bir `.exe` dosyasıdır. Python veya başka bir bağımlılık gerektirmez.  
- Yaklaşık 20 MB depolama alanı yeterlidir.

***

## 🛠 **Geliştirme Detayları**

**Teknolojiler**:  
- **Python 3.10+**
- **ttkbootstrap**: Modern kullanıcı arayüzü için.
- **requests**: Diyanet API çağrıları için.
- **BeautifulSoup**: HTML verilerini işlemek için.

**Ana Dosyalar**:
- `main.py`: Uygulamanın ana mantığını içerir.
- `settings.json` ve `vakitler.json`: Uygulama verilerinin depolandığı dosyalar.

***

## ✨ **Özelleştirme**

Seher uygulamasını tamamen size özel hale getirebilirsiniz:
- **Renkler ve temalar**: Kendi renk şemanızı ayarlayın. Göz yormayan seçenekler mevcut!
- **Kritik uyarı süreleri**: Namaz vaktine ne kadar süre kala uyarı çıkacağını seçin.
- **Görünüm seçimi**: Yatay veya dikey tasarımla kullanımı isteğinize göre şekillendirin.
- **Saniye gösterimi**: Daha sade bir saat gösterimi için saniyeleri kapatabilirsiniz.

***

## 🧩 **Bilinen Hatalar**

- **İlk Çalıştırma**: `ayarlar.json` veya `vakitler.json` dosyalarının oluşmaması durumunda uygulama kapanabilir. Bu dosyalar otomatik oluşturulacaktır.
- **Bağlantı Hatası**: Bazı durumlarda Diyanet İşleri Başkanlığı’nın servisi yanıt vermeyebilir. (Nadir görülen bir durum.)

***

## 🌟 **Gelecekteki Planlar**

Seher uygulaması daha fazla özellik ve destekle güncellenmeye devam edecek:
- **Android/iOS versiyonları**
- Daha fazla tema ve özelleştirme
- Ek çoklu dil desteği (İngilizce, Almanca, Arapça vb.)
- Günlük hadis ve dualar entegrasyonu

***

## 🎯 **Katkıda Bulunun**

Bu projeyi geliştirmek için katkıda bulunmak ister misiniz? Pull request'ler her zaman açıktır!  
Ayrıca hatalar, öneriler veya iyileştirmeler ile ilgili [issues](https://github.com/alitekdemir/Seher/issues) sayfamızı kullanabilirsiniz.

**Adımlar**:
1. Bu repository'yi fork'layın.
2. Değişikliklerinizi yapın.
3. Bir pull request açarak katkılarınızı paylaşın.

***

## 📬 **İletişim**

Herhangi bir öneri veya sorunuz varsa, bize ulaşmaktan çekinmeyin:  
📧 **ali.tekdemir@gmail.com**  
📂 **[GitHub Proje Sayfası](https://github.com/alitekdemir/Seher)**  

**Destekleriniz için Teşekkürler!** 🌟  
