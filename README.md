## Takım & Ürün İsmi
<h1>RadiGlow</h1>

## 👥 Takımımız
|    | <div align="center">İsim</div>   | <div align="center">Rol</div>  | <div align="center">Sosyal Medya</div>     |
| :-----------: | :---------- | :---------- | :----------: |
|<img src="https://media.licdn.com/dms/image/v2/D4D03AQHJdXnh3RzhMA/profile-displayphoto-shrink_800_800/B4DZabQWAJGsAg-/0/1746361475913?e=1757548800&v=beta&t=b9Qn4X3kXCsNUrl9SIM-wm1Btt1fscIdb_ASbyPvsuU" alt="Profil Fotoğrafı" width="100"/>  | Ibrahim Mammadli| Product Owner/Developer     | [![linkedin](https://github.com/user-attachments/assets/3baa645a-33bc-4786-8327-cb0f92356f0a)](https://www.linkedin.com/in/ibrahim-mammadly/)   | 
|<img src="https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png" alt="Foto" width="100"/>  | Meliha Atasoy    | Scrum Master     |  [![linkedin](https://github.com/user-attachments/assets/3baa645a-33bc-4786-8327-cb0f92356f0a)](https://www.linkedin.com/in/meliha-atasoy-70a8a428b/) |
|<img src="https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png" alt="Foto" width="100"/> | Zeynep Yıldız    | Developer      |  [![linkedin](https://github.com/user-attachments/assets/3baa645a-33bc-4786-8327-cb0f92356f0a)](#)   |
|<img src="https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png" alt="Foto" width="100"/>| Ahmet Özçelik    | Developer     |    [![linkedin](https://github.com/user-attachments/assets/3baa645a-33bc-4786-8327-cb0f92356f0a)](#)    |

## Ürün Logosu
<img src="https://github.com/nicefaa6waa/yzta_gr82/blob/a30f988be0c7067f9ceca6161b9c001c223e9864/59ef216c-bb6b-447e-9dbd-1b93594890ad.jpeg" alt="RadiGlow Logo" width="200"/>
## Genel Bakış

Bu repo, **BLIP2-OPT-6.7B** modelinin radyoloji görüntüleri için tanımlayıcı alt yazılar oluşturmak üzere uygulanmasına odaklanmaktadır. Proje, tıbbi görüntü alt yazıları için **Radiology Object in Context Version 2 (ROCOv2)** adlı tıbbi veri seti üzerinde ince ayar yapılmış bir görme-dil modelini kullanır. Hesaplama kısıtlamalarını aşmak için **Parameter-Efficient Fine-Tuning (PEFT)** kullanılmış, bu da büyük modelin tıbbi alana verimli bir şekilde uyarlanmasını sağlamıştır.

---

## Uyarı

Bu proje **sadece araştırma ve öğrenme amaçlı** olarak gerçekleştirilmiştir ve bootcamp projem olarak sunulmaktadır. **Sınırlı hesaplama kaynakları** nedeniyle, model, **iki adet NIVIDA Tesla T4 GPU** kullanılarak azaltılmış sayıda epoch ile henüz eğitilmemiştir.

---

## Veri Seti: ROCOv2

### Veri Seti Boyutu

- **Orijinal Veri Seti:**

  - **Training Set:** 59,958 görüntü
  - **Validation Set:** 9,904 görüntü
  - **Test Set:** 9,927 görüntü

- **Filtrelenmiş Veri Seti (RGB-Only):**
  - **Training Set:** 37,330 görüntü
  - **Validation Set:** 6,672 görüntü
  - **Test Set:** 6,780 görüntü

İşlemeyi basitleştirmek ve hesaplama karmaşıklığını azaltmak için veri setinden sadece RGB görüntüleri seçilmiştir, bu da veri seti boyutunun azalmasına yol açmıştır.

---

## Model: BLIP2-OPT-6.7B

BLIP2 (Bootstrapped Language-Image Pre-training) bir görme-dil modelidir ve görüntü ile metin temsillerini birleştirir. Bu proje için **BLIP2-OPT-6.7B** varyantı kullanılmıştır ve şu özelliklere sahiptir:

- **Vision Encoder:** Önceden eğitilmiş görsel omurga, özellik çıkarma için.
- **Language Model:** OPT-6.7B, metinsel alt yazılar oluşturmak için optimize edilmiş.
- **Parameter-Efficient Fine-Tuning (PEFT):** Tıbbi alana uyum sağlamak için büyük modelin tüm parametrelerini tamamen eğitmeden, hesaplama maliyetlerini önemli ölçüde azaltarak uygulanmıştır.

---

## Yöntem

### Ön İşleme

1. **Veri Seti Filtreleme:**

   - Sadece ROCOv2 veri setinden RGB görüntüleri dahil edilmiştir.
   - Görüntüler ön işleme sırasında yeniden boyutlandırılmış ve normalize edilmiştir.

2. **Caption Tokenization:**
   - Alt yazılar, BLIP2-OPT modeli ile uyumlu bir formata tokenlaştırılmıştır.

### Eğitim

1. **PEFT ile İnce Ayar:**

   - **Parameter-Efficient Fine-Tuning (PEFT):**
     - Sadece model parametrelerinin bir alt kümesi ince ayar yapılmış, çoğunlukla önceden eğitilmiş parametreler dondurulmuştur.
     - **LoRA (Low-Rank Adaptation)** gibi teknikler, tıbbi alana verimli bir şekilde uyum sağlamak için kullanılacaktır.
   - **Donanım:** Eğitim, henüz tamamlanmamış olmakla birlikte, iki **NVIDIA T4 GPU** üzerinde gerçekleştirilecektir.
   - **Eğitim Epochları:** Donanım kısıtlamalarına uyum sağlamak için azaltılmış sayıda epoch planlanmıştır.
   - **Optimizasyon ve Zamanlayıcı:** Tıbbi alan ince ayarı için yapılandırılacaktır.
   - **Batch Boyutu:** GPU bellek sınırlarına göre ayarlanacaktır.

2. **Doğrulama:**

   - Performans, eğitim sırasında validation seti üzerinde izlenerek overfitting önlenecektir.

3. **Test:**
   - Modelin nihai performansı, test seti üzerinde değerlendirilecek ve doğru alt yazılar oluşturmaya odaklanılacaktır.

---
## YZTA Sprint Raporları
[Sprint Backlog](https://docs.google.com/spreadsheets/d/186WY3a52Ao72XRL9WEF60SxfzfMMOr-pQLSANZt3_ZM/edit?gid=0#gid=0)

### Sprint Hedefleri
  - AI modelinin röntgen görüntülerini sınıflandırma doğruluğunu artırma
  - Kullanıcı arayüzünde raporlama özelliği ekleme
  - Backend API’lerini optimize etme
  - Test senaryolarını tamamlama
### Tahmin Edilen Tamamlanacak Puan (Story Points)
  - Toplam Puan:100p
    - Front-end: 8p
    - Back-end: 10p
    - Model optimization: 9p
    - Mobile App Development: 8p
    - Mobile App Development (IOS): 8p
    - Uygulama Prosedürü:5p
    - AI Entegrasyonu: 7p
    - Scrum Master Coordination:3p
### Tahmin Mantığı:
  - Önceki sprintlerdeki hız (velocity) dikkate alınarak 
  - Karmaşık AI işleri daha yüksek puanlandı
  - UI ve test işleri daha düşük puanla tahmin edildi

### DAİLY SCRUM
  - AI model eğitim verileri hazırlandı
  - Raporlama arayüzü tasarlandı
  - Backend optimizasyon başladı
  - Model doğruluk testleri yapıldı
  - Sprint review hazırlıkları

### Sprint Board Güncellemeleri
Görev	Durum	Notlar
AI Model Fine-Tuning	Devam Ediyor	Doğruluk %92’ye çıktı
Raporlama UI	Devam Ediyor	Son testler yapılıyor
Backend Optimizasyon	Beklemede	Response time %30 azaldı
Test Senaryoları	Beklemede	API testleri tamamlandı


### Sprint Review & Retrospective
#### Başarılar:
  - Model doğruluğu hedefe yaklaştı 
  - Backend optimizasyon tamamlandı
#### Geliştirilecek Noktalar:
  - GPU kaynakları artırılmalı
  - QA süreci daha erken başlatılmalı
#### Aksiyonlar:
  - Cloud GPU kaynağı için yeni bir platform bulunacak
  - Bir sonraki sprintte testler daha erken başlatılacak
## Gelecek Çalışmalar

- **Veri Seti Kapsamını Genişletme:** Gri tonlamalı görüntüleri ekleyerek veri seti çeşitliliğini artırma.
- **Eğitim Optimizasyonu:** Daha fazla GPU veya bulut tabanlı kaynaklar kullanarak daha uzun eğitim oturumları ve hiperparametre ayarı yapma.
- **Daha Büyük Mimari Denemeleri:** Alt yazı oluşturma kalitesini iyileştirmek için daha büyük vision-language modelleriyle deneme yapma.
- **Advanced PEFT Teknikleri:** Eğitim performansını daha da optimize etmek için gelişmiş parameter-efficient teknikler deneme.

---

## Teşekkürler

- **Model:** [BLIP2-OPT-6.7B](https://huggingface.co/Salesforce/blip2-opt-6.7b)
- **Veri Seti:** [ROCOv2](https://github.com/sctg-development/ROCOv2-radiology)

Bu proje, en son teknoloji vision-language modellerini kullanarak tıbbi görüntü alt yazıları oluşturmanın bir demonstrasyonu olarak hizmet vermektedir ve gerçek dünya klinik uygulamaları için tasarlanmamıştır.
