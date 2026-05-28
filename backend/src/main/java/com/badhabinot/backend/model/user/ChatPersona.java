package com.badhabinot.backend.model.user;

/**
 * Sohbet asistanının kullanıcıya karşı kişiliği.
 *
 * <ul>
 *   <li>{@link #GENERAL_CHAT} — Doğal sohbet (varsayılan). Asistan günlük
 *       konularda normal bir AI gibi konuşur; monitoring verisi yalnızca
 *       kullanıcı doğrudan sorduğunda dahil edilir.</li>
 *   <li>{@link #BEHAVIOR_COACH} — Davranış koçluğu. Her yanıt monitoring
 *       verisine bağlıdır; klasik "bugün şu skor, dikkat" akışı.</li>
 *   <li>{@link #CUSTOM} — Kullanıcının kendi system promptu kullanılır;
 *       özelleştirilebilir ileri kullanım.</li>
 * </ul>
 */
public enum ChatPersona {
    GENERAL_CHAT,
    BEHAVIOR_COACH,
    CUSTOM
}
