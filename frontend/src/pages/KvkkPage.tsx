import { Link } from 'react-router-dom'
import { ChevronLeft, ShieldCheck } from 'lucide-react'
import { useLanguage } from '@/i18n/language-provider'

export function KvkkPage() {
  const { isTurkish } = useLanguage()

  return (
    <div className="min-h-screen bg-[var(--bg-base)] px-5 py-10 md:px-8">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/onboarding"
          className="mb-8 inline-flex items-center gap-2 text-sm text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
        >
          <ChevronLeft size={14} />
          {isTurkish ? 'Geri dön' : 'Go back'}
        </Link>

        <div className="mb-8 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl bg-[var(--primary)] bg-opacity-10">
            <ShieldCheck size={20} className="text-[var(--primary)]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-strong)]">KVKK Aydınlatma Metni</h1>
            <p className="text-sm text-[var(--text-muted)]">
              6698 sayılı Kişisel Verilerin Korunması Kanunu
            </p>
          </div>
        </div>

        <div className="space-y-8 text-sm leading-7 text-[var(--text-muted)]">
          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">1. Veri Sorumlusu</h2>
            <p>
              Bu aydınlatma metni, <strong className="text-[var(--text-strong)]">BADHABINOT</strong> uygulaması
              kapsamında 6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") uyarınca hazırlanmıştır.
              Uygulama, kişisel sağlık ve davranış verilerinizi işleyen bir platform olup veri sorumlusu
              sıfatıyla hareket etmektedir.
            </p>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">2. İşlenen Kişisel Veriler</h2>
            <ul className="ml-4 list-disc space-y-1">
              <li><strong className="text-[var(--text-strong)]">Kimlik verileri:</strong> Ad-soyad, e-posta adresi</li>
              <li><strong className="text-[var(--text-strong)]">Cihaz ve oturum verileri:</strong> IP adresi, oturum süreleri, tarayıcı bilgisi</li>
              <li><strong className="text-[var(--text-strong)]">Görüntü verileri:</strong> Kamera aracılığıyla elde edilen anlık kare görüntüleri (yalnızca analiz süresince; kalıcı olarak depolanmaz)</li>
              <li><strong className="text-[var(--text-strong)]">Davranış analiz verileri:</strong> Poz tahmini, el hareketi skorları, sigara benzeri jest sinyalleri</li>
              <li><strong className="text-[var(--text-strong)]">Sağlık alışkanlığı verileri:</strong> Su tüketimi kayıtları, oturma düzeni uyarıları</li>
              <li><strong className="text-[var(--text-strong)]">Konum/zaman dilimi:</strong> Bildirim ve analiz zaman damgaları için</li>
            </ul>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">3. Kişisel Verilerin İşlenme Amaçları</h2>
            <ul className="ml-4 list-disc space-y-1">
              <li>Canlı davranış izleme ve analiz hizmeti sunmak</li>
              <li>Kullanıcı oturumu ve hesap güvenliğini sağlamak</li>
              <li>Su içme, duruş ve dinlenme hatırlatıcıları göndermek</li>
              <li>Geçmiş davranış verilerine dayalı raporlar oluşturmak</li>
              <li>Harici AI sağlayıcısı aracılığıyla görüntü analizi yapmak (açık onayınızla)</li>
              <li>Yasal yükümlülükleri yerine getirmek</li>
            </ul>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">4. Kişisel Verilerin İşlenme Hukuki Dayanağı</h2>
            <p>
              Verileriniz; <em>açık rızanız</em> (KVKK m.5/1), <em>sözleşmenin ifası</em> (KVKK m.5/2-c)
              ve <em>meşru menfaat</em> (KVKK m.5/2-f) hukuki sebeplerine dayalı olarak işlenmektedir.
              Görüntü ve davranış verileri yalnızca açık onayınız alındıktan sonra işlenir.
            </p>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">5. Kişisel Verilerin Aktarımı</h2>
            <p>
              Anlık kare görüntüleri ve davranış sinyalleri, yalnızca açık uzak çıkarım onayınızın
              bulunması hâlinde harici AI analiz servisine aktarılır. Görüntü ön işleme adımı (<em>vision-service</em>)
              yerel altyapıda gerçekleştirilir; ham görüntü depolanmaz. Harici aktarım OpenAI uyumlu
              API uç noktası üzerinden şifreli olarak yapılır.
            </p>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">6. Kişisel Verilerin Saklanma Süresi</h2>
            <ul className="ml-4 list-disc space-y-1">
              <li>Kamera kareleri: İşlem tamamlandıktan hemen sonra silinir, kalıcı depolama yapılmaz</li>
              <li>Davranış olayları ve oturum kayıtları: Hesap aktif olduğu sürece saklanır</li>
              <li>Hesap silindiğinde tüm kişisel veriler 30 gün içinde kalıcı olarak imha edilir</li>
            </ul>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">7. KVKK Kapsamındaki Haklarınız</h2>
            <p className="mb-2">KVKK'nın 11. maddesi uyarınca aşağıdaki haklara sahipsiniz:</p>
            <ul className="ml-4 list-disc space-y-1">
              <li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
              <li>Kişisel verileriniz işlenmişse buna ilişkin bilgi talep etme</li>
              <li>İşlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme</li>
              <li>Yurt içinde veya yurt dışında kişisel verilerinizin aktarıldığı üçüncü kişileri bilme</li>
              <li>Kişisel verilerinizin eksik veya yanlış işlenmiş olması hâlinde bunların düzeltilmesini isteme</li>
              <li>Kişisel verilerinizin silinmesini veya yok edilmesini isteme</li>
              <li>İşlenen verilerin münhasıran otomatik sistemler vasıtasıyla analiz edilmesi suretiyle aleyhinize bir sonucun ortaya çıkmasına itiraz etme</li>
              <li>Kişisel verilerinizin kanuna aykırı olarak işlenmesi sebebiyle zarara uğramanız hâlinde zararın giderilmesini talep etme</li>
            </ul>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">8. Başvuru Yolu</h2>
            <p>
              Yukarıda belirtilen haklarınızı kullanmak için uygulama içi hesap ayarlarından veya
              aşağıdaki kanallar aracılığıyla başvurabilirsiniz. Başvurularınız, KVKK'nın 13. maddesi
              uyarınca en geç <strong className="text-[var(--text-strong)]">30 gün</strong> içinde
              yanıtlanacaktır.
            </p>
          </section>

          <section>
            <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">9. Değişiklikler</h2>
            <p>
              Bu aydınlatma metni, yasal düzenlemeler veya platform özellikleri değiştikçe güncellenebilir.
              Önemli değişikliklerde kullanıcılar uygulama üzerinden bilgilendirilecektir.
            </p>
          </section>

          <p className="text-xs text-[var(--text-muted)]">
            Son güncelleme: Mayıs 2026
          </p>
        </div>
      </div>
    </div>
  )
}
