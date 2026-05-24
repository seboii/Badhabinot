/**
 * KVKK Aydınlatma Metni — single source of truth.
 * Used by both KvkkModal (registration) and KvkkPage (standalone route).
 */

export type KvkkSection = {
  heading: string
  body: string[]
}

export const KVKK_SECTIONS_TR: KvkkSection[] = [
  {
    heading: '1. Veri Sorumlusu',
    body: [
      'Bu aydınlatma metni, BADHABINOT uygulaması kapsamında 6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") uyarınca hazırlanmıştır. Uygulama, kişisel sağlık ve davranış verilerinizi işleyen bir platform olup veri sorumlusu sıfatıyla hareket etmektedir.',
    ],
  },
  {
    heading: '2. İşlenen Kişisel Veriler',
    body: [
      'a) Kimlik Bilgileri: Ad-soyad, e-posta adresi',
      'b) Biyometrik Veriler: Yüz görüntüsü ve yüz tanıma verileri (face embeddings). Yüz verileriniz yalnızca platform sunucusunda şifreli olarak saklanır; üçüncü taraflarla paylaşılmaz.',
      'c) Sağlık ve Davranış Verileri: Oturuş pozisyonu analizi, el hareketleri tespiti, uyku/uyanıklık durumu (göz takibi), su içme alışkanlıkları, sigara benzeri hareket tespiti.',
      'd) Kullanım Verileri: Oturum süreleri, uygulama kullanım istatistikleri.',
      'e) Kamera Görüntüleri: Gerçek zamanlı analiz için kullanılır. Ham görüntüler kalıcı olarak depolanmaz; yalnızca analiz sonuçları kaydedilir.',
    ],
  },
  {
    heading: '3. Verilerin İşlenme Amaçları',
    body: [
      '• Davranış izleme ve analiz hizmeti sunmak',
      '• Kişiselleştirilmiş sağlık önerileri oluşturmak',
      '• Yüz tanıma ile güvenli kimlik doğrulama sağlamak',
      '• Su içme, duruş ve dinlenme hatırlatıcıları göndermek',
      '• Geçmiş davranış verilerine dayalı raporlar oluşturmak',
      '• Yasal yükümlülükleri yerine getirmek',
    ],
  },
  {
    heading: '4. Kişisel Verilerin İşlenme Hukuki Dayanağı',
    body: [
      'Verileriniz; açık rızanız (KVKK m.5/1), sözleşmenin ifası (KVKK m.5/2-c) ve meşru menfaat (KVKK m.5/2-f) hukuki sebeplerine dayalı olarak işlenmektedir. Görüntü ve biyometrik veriler yalnızca açık onayınız alındıktan sonra işlenir.',
    ],
  },
  {
    heading: '5. Verilerin Saklanması ve Güvenliği',
    body: [
      '• Verileriniz şifreli olarak saklanır.',
      '• Yüz embedding verileri geri dönüştürülemez matematiksel vektörler olarak tutulur; ham yüz fotoğrafı saklanmaz.',
      '• Kamera görüntüleri işlendikten hemen sonra bellekten silinir, kalıcı depolama yapılmaz.',
      '• Verileriniz yalnızca sizin erişebileceğiniz hesabınızda tutulur.',
    ],
  },
  {
    heading: '6. Kişisel Verilerin Aktarımı',
    body: [
      'Kişisel verileriniz üçüncü taraflarla paylaşılmaz. Yapay zeka analizi için görüntü ön işleme adımı (vision-service) yerel altyapıda gerçekleştirilir. Uzak çıkarım onayınızın bulunması hâlinde yalnızca davranış sinyalleri harici AI servisine şifreli olarak iletilir; ham görüntü asla gönderilmez. Yasal zorunluluk dışında hiçbir kurum veya kuruluşla paylaşım yapılmaz.',
    ],
  },
  {
    heading: '7. KVKK Kapsamındaki Haklarınız (Madde 11)',
    body: [
      '• Kişisel verilerinizin işlenip işlenmediğini öğrenme',
      '• İşlenmişse buna ilişkin bilgi talep etme',
      '• İşlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme',
      '• Yurt içinde veya yurt dışında aktarıldığı üçüncü kişileri bilme',
      '• Eksik veya yanlış işlenmiş olması hâlinde düzeltilmesini isteme',
      '• KVKK Madde 7\'deki şartlar çerçevesinde silinmesini veya yok edilmesini isteme',
      '• Düzeltme/silme işlemlerinin aktarıldığı üçüncü kişilere bildirilmesini isteme',
      '• Münhasıran otomatik sistemlerle analiz edilmesi sonucu aleyhinize çıkan sonuca itiraz etme',
      '• Kanuna aykırı işlenmesi sebebiyle zarara uğramanız hâlinde zararın giderilmesini talep etme',
    ],
  },
  {
    heading: '8. Hesap Silme ve Veri İmhası',
    body: [
      'Hesabınızı istediğiniz zaman Ayarlar sayfasından silebilirsiniz. Hesap silindiğinde tüm kişisel verileriniz, yüz tanıma verileri dahil, kalıcı olarak imha edilir. Bu işlem geri alınamaz.',
    ],
  },
  {
    heading: '9. Başvuru ve İletişim',
    body: [
      'Yukarıdaki haklarınızı kullanmak için uygulama içi hesap ayarlarından başvurabilirsiniz. Başvurularınız KVKK\'nın 13. maddesi uyarınca en geç 30 gün içinde yanıtlanacaktır.',
    ],
  },
  {
    heading: '10. Değişiklikler',
    body: [
      'Bu aydınlatma metni, yasal düzenlemeler veya platform özellikleri değiştikçe güncellenebilir. Önemli değişikliklerde kullanıcılar uygulama üzerinden bilgilendirilecektir.',
      'Son güncelleme: Mayıs 2026',
    ],
  },
]

export const KVKK_SECTIONS_EN: KvkkSection[] = [
  {
    heading: '1. Data Controller',
    body: [
      'This disclosure is prepared under Law No. 6698 on the Protection of Personal Data (KVKK) for the BADHABINOT application. The platform processes personal health and behavioral data and acts as the data controller.',
    ],
  },
  {
    heading: '2. Personal Data Processed',
    body: [
      'a) Identity Data: Full name, e-mail address',
      'b) Biometric Data: Facial image and face recognition data (face embeddings). Your face data is stored encrypted on the platform server only and is never shared with third parties.',
      'c) Health & Behavioral Data: Posture analysis, hand movement detection, drowsiness/alertness (eye tracking), hydration habits, smoking-like gesture detection.',
      'd) Usage Data: Session durations, application usage statistics.',
      'e) Camera Frames: Used for real-time analysis only. Raw frames are not stored permanently; only analysis results are saved.',
    ],
  },
  {
    heading: '3. Purposes of Processing',
    body: [
      '• To provide behavior monitoring and analysis services',
      '• To generate personalized health recommendations',
      '• To enable secure identity verification via face recognition',
      '• To send hydration, posture, and break reminders',
      '• To generate reports based on historical behavior data',
      '• To fulfill legal obligations',
    ],
  },
  {
    heading: '4. Legal Basis for Processing',
    body: [
      'Your data is processed based on your explicit consent (KVKK Art. 5/1), performance of a contract (Art. 5/2-c), and legitimate interest (Art. 5/2-f). Biometric and image data is processed only after obtaining your explicit consent.',
    ],
  },
  {
    heading: '5. Data Storage and Security',
    body: [
      '• Your data is stored in encrypted form.',
      '• Face embedding data is stored as irreversible mathematical vectors; no raw face photos are saved.',
      '• Camera frames are deleted from memory immediately after processing; no permanent storage occurs.',
      '• Your data is accessible only within your own account.',
    ],
  },
  {
    heading: '6. Data Transfers',
    body: [
      'Your personal data is not shared with third parties. Vision preprocessing runs on local infrastructure. When you have granted remote inference consent, only behavioral signals (not raw images) are transmitted to the external AI service in encrypted form. No sharing occurs with any institution except as legally required.',
    ],
  },
  {
    heading: '7. Your Rights Under KVKK (Article 11)',
    body: [
      '• To learn whether your personal data is being processed',
      '• To request information if it is processed',
      '• To learn the purpose and whether it is used accordingly',
      '• To know the third parties to whom data is transferred',
      '• To request correction of incomplete or incorrect data',
      '• To request deletion or destruction under KVKK Art. 7',
      '• To request notification of corrections/deletions to third parties',
      '• To object to results arising solely from automated analysis',
      '• To claim compensation for damages from unlawful processing',
    ],
  },
  {
    heading: '8. Account Deletion and Data Erasure',
    body: [
      'You may delete your account at any time from the Settings page. Upon account deletion, all personal data including biometric data will be permanently erased. This action cannot be undone.',
    ],
  },
  {
    heading: '9. Contact',
    body: [
      'To exercise the above rights, you may apply through the in-app account settings. Requests will be answered within 30 days as required by KVKK Art. 13.',
    ],
  },
  {
    heading: '10. Changes',
    body: [
      'This disclosure may be updated when laws or platform features change. Users will be notified of material changes through the application.',
      'Last updated: May 2026',
    ],
  },
]
