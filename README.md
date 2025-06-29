# BLIP2-OPT-6.7B ile Medical Image Captioning

## Genel Bakış

Bu repo, **BLIP2-OPT-6.7B** modelinin radyoloji görüntüleri için tanımlayıcı alt yazılar oluşturmak üzere uygulanmasına odaklanmaktadır. Proje, tıbbi görüntü alt yazıları için **Radiology Object in Context Version 2 (ROCOv2)** adlı tıbbi veri seti üzerinde ince ayar yapılmış bir görme-dil modelini kullanır. Hesaplama kısıtlamalarını aşmak için **Parameter-Efficient Fine-Tuning (PEFT)** kullanılmış, bu da büyük modelin tıbbi alana verimli bir şekilde uyarlanmasını sağlamıştır.

---

## Uyarı

Bu proje **sadece araştırma ve öğrenme amaçlı** olarak gerçekleştirilmiştir ve bootcamp projem olarak sunulmaktadır. **Sınırlı hesaplama kaynakları** nedeniyle, model, **tek bir NVIDIA V100 GPU** kullanılarak azaltılmış sayıda epoch ile henüz eğitilmemiştir.

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

## Gelecek Çalışmalar

- **Veri Seti Kapsamını Genişletme:** Gri tonlamalı görüntüleri ekleyerek veri seti çeşitliliğini artırma.
- **Eğitim Optimizasyonu:** Daha fazla GPU veya bulut tabanlı kaynaklar kullanarak daha uzun eğitim oturumları ve hiperparametre ayarı yapma.
- **Daha Büyük Mimari Denemeleri:** Alt yazı oluşturma kalitesini iyileştirmek için daha büyük vision-language modelleriyle deneme yapma.
- **Advanced PEFT Teknikleri:** Eğitim performansını daha da optimize etmek için gelişmiş parameter-efficient teknikler deneme.

---

## Teşekkürler

- **Model:** [BLIP2-OPT-6.7B](https://huggingface.co/Salesforce/blip2-opt-6.7b)
- **Veri Seti:** [ROCOv2](https://github.com/radiclinic/roco)

Bu proje, en son teknoloji vision-language modellerini kullanarak tıbbi görüntü alt yazıları oluşturmanın bir demonstrasyonu olarak hizmet vermektedir ve gerçek dünya klinik uygulamaları için tasarlanmamıştır.