# 🌟 RadiGlow - Radyoloji AI Captioning

## 👥 Takımımız
|    | <div align="center">İsim</div>   | <div align="center">Rol</div>  | <div align="center">Sosyal Medya</div>     |
| :-----------: | :---------- | :---------- | :----------: |
|<img src="https://media.licdn.com/dms/image/v2/D4D03AQHJdXnh3RzhMA/profile-displayphoto-shrink_800_800/B4DZabQWAJGsAg-/0/1746361475913?e=1757548800&v=beta&t=b9Qn4X3kXCsNUrl9SIM-wm1Btt1fscIdb_ASbyPvsuU" alt="İbrahim Foto" width="100"/>  | Ibrahim Mammadli | Project Manager/Developer     | [![linkedin](https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ibrahim-mammadly/)   | 
|<img src="https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png" alt="Meliha Foto" width="100"/>  | Meliha Atasoy    | Scrum Master     |  [![linkedin](https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/meliha-atasoy-70a8a428b/) |
|<img src="https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png" alt="Zeynep Foto" width="100"/> | Zeynep Yıldız    | Developer     |  [![linkedin](https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white)](#)   |
|<img src="https://cdn.pixabay.com/photo/2016/08/08/09/17/avatar-1577909_960_720.png" alt="Ahmet Foto" width="100"/>| Ahmet Özçelik     | Developer     |    [![linkedin](https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white)](#)    |


## 🎨 Ürün Logosu
![RadiGlow Logosu](https://github.com/nicefaa6waa/yzta_gr82/blob/a30f988be0c7067f9ceca6161b9c001c223e9864/59ef216c-bb6b-447e-9dbd-1b93594890ad.jpeg)

---

## 🌐 Genel Bakış

Bu depo, **BLIP2-OPT-6.7B** modelinin radyoloji görüntüleri için tanımlayıcı alt yazılar oluşturmak üzere uygulanmasına odaklanmaktadır. Proje, tıbbi görüntü alt yazıları için **Radyoloji Nesneleri Bağlamda Sürüm 2 (ROCOv2)** adlı tıbbi veri seti üzerinde ince ayar yapılmış bir görme-dil modelini kullanır. Hesaplama kısıtlamalarını aşmak için **Parametre-Etkili İnce Ayar (PEFT)** kullanılmış, bu da büyük modelin tıbbi alana verimli bir şekilde uyarlanmasını sağlamıştır.

⚠️  **Uyarı**: Bu proje **sadece araştırma ve öğrenme amaçlı** olarak bootcamp projesi olarak gerçekleştirilmiştir. **Sınırlı hesaplama kaynakları** nedeniyle, model, henüz iki **NVIDIA Tesla T4 GPU** kullanılarak azaltılmış epoch ile eğitilmemiştir.

---

## 📊 Veri Seti: ROCOv2

### Veri Seti Boyutu
- **Orijinal Veri Seti**:
  - **Eğitim Seti**: 59.958 görüntü
  - **Doğrulama Seti**: 9.904 görüntü
  - **Test Seti**: 9.927 görüntü
- **Filtrelenmiş Veri Seti (Sadece RGB)**:
  - **Eğitim Seti**: 37.330 görüntü
  - **Doğrulama Seti**: 6.672 görüntü
  - **Test Seti**: 6.780 görüntü

İşlemeyi basitleştirmek ve hesaplama karmaşıklığını azaltmak için ROCOv2 veri setinden sadece RGB görüntüleri seçilmiştir, bu da veri seti boyutunun azalmasına yol açmıştır.

---

## 🤖 Model: BLIP2-OPT-6.7B

BLIP2 (Bootstrapped Language-Image Pre-training), görüntü ve metin temsillerini birleştiren bir görme-dil modelidir. Bu proje için **BLIP2-OPT-6.7B** varyantı kullanılmıştır ve şu özelliklere sahiptir:

- **Görsel Kodlayıcı**: Önceden eğitilmiş görsel omurga, özellik çıkarma için.
- **Dil Modeli**: OPT-6.7B, metinsel alt yazılar oluşturmak için optimize edilmiş.
- **Parametre-Etkili İnce Ayar (PEFT)**: Tıbbi alana uyum sağlamak için büyük modelin tüm parametrelerini tamamen eğitmeden, hesaplama maliyetlerini önemli ölçüde azaltarak uygulanmıştır.

---

## 🛠️ Yöntem

### Ön İşleme
1. **Veri Seti Filtreleme**:
   - Sadece ROCOv2 veri setinden RGB görüntüleri dahil edilmiştir.
   - Görüntüler ön işleme sırasında yeniden boyutlandırılmış ve normalize edilmiştir.
2. **Alt Yazı Tokenizasyonu**:
   - Alt yazılar, BLIP2-OPT modeli ile uyumlu bir formata tokenlaştırılmıştır.

### Eğitim
1. **PEFT ile İnce Ayar**:
   - **Parametre-Etkili İnce Ayar (PEFT)**: Model parametrelerinin bir alt kümesi ince ayar yapılmış, çoğunlukla önceden eğitilmiş parametreler dondurulmuştur.
   - **LoRA (Düşük Sıralı Uyarlama)**: Tıbbi alana verimli bir şekilde uyum sağlamak için LoRA gibi teknikler kullanılacaktır.
   - **Donanım**: Eğitim, henüz tamamlanmamış olmakla birlikte, iki **NVIDIA T4 GPU** üzerinde gerçekleştirilecektir.
   - **Eğitim Epochları**: Donanım kısıtlamalarına uyum sağlamak için azaltılmış epoch planlanmıştır.
   - **Optimizasyon ve Zamanlayıcı**: Tıbbi alan ince ayarı için yapılandırılacaktır.
   - **Batch Boyutu**: GPU bellek sınırlarına göre ayarlanacaktır.
2. **Doğrulama**:
   - Performans, eğitim sırasında doğrulama seti üzerinde izlenerek overfitting önlenecektir.
3. **Test**:
   - Modelin nihai performansı, test seti üzerinde değerlendirilecek ve doğru alt yazılar oluşturmaya odaklanılacaktır.

---

## 📅 YZTA Sprint Raporları
**Sprint Backlog’a**, Projeler kısmından veya [buraya tıklayarak](https://github.com/users/nicefaa6waa/projects/1) ulaşabilirsiniz.

**Sprint İnceleme ve Retrospektif** dosyasına, Projeler kısmından veya [buraya tıklayarak](https://github.com/users/nicefaa6waa/projects/2) ulaşabilirsiniz.

**Fotoğraflar ve Günlük Scrum Güncellemeleri'ne**, Projeler kısmından veya [buraya tıklayarak](https://github.com/users/nicefaa6waa/projects/3) ulaşabilirsiniz.


---

## 🙏 Teşekkürler
- **Model**: [BLIP2-OPT-6.7B](https://huggingface.co/Salesforce/blip2-opt-6.7b)
- **Veri Seti**: [ROCOv2](https://github.com/sctg-development/ROCOv2-radiology)

Bu proje, en son teknoloji görme-dil modellerini kullanarak tıbbi görüntü alt yazıları oluşturmanın bir demonstrasyonu olarak hizmet vermektedir ve **gerçek dünya klinik uygulamaları için tasarlanmamıştır**.
