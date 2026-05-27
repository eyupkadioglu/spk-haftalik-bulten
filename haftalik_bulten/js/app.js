(function () {
  'use strict';

  const STORAGE_KEY = 'spk_haftalik_bulten_v2';

  const ROLE_LABELS = {
    ADMIN: 'Admin',
    KB: 'Kurul Başkanı',
    KBY: 'Başkan Yardımcısı',
    KOB: 'Kurul Özel Bürosu',
    KOB_PERSONELI: 'Kurul Özel Büro Personeli',
    DB: 'Daire Başkanı',
    DBY: 'Daire Başkan Yrd.'
  };

  const ROLE_SWITCHER_LABELS = {
    DBY: 'Daire Başkan Yrd.'
  };

  const ROLE_RANK = {
    ADMIN: 0, KB: 1, KOB: 2, KOB_PERSONELI: 2, KBY: 3, DB: 4, DBY: 5
  };

  const ROLE_SUPERIOR = {
    DBY: 'DB',
    KOB_PERSONELI: 'KOB', DB: 'KBY', KOB: 'KB'
  };

  const ENTRY_STATUS_LABELS = {
    DRAFT: 'Taslak', PENDING: 'Onay Bekliyor', APPROVED: 'Onaylandı', RETURNED: 'İade'
  };

  const STATUS_LABELS = {
    DRAFT: 'Taslak',
    SECTION_PREP: 'Daire Hazırlığında',
    DBY_REVIEW: 'Daire Başkan Yrd. Kontrolü Bekliyor',
    DB_APPROVAL: 'Daire Başkanı Onayı Bekliyor',
    KBY_APPROVAL: 'Başkan Yardımcısı Onayı Bekliyor',
    KBY_APPROVED: 'Kurul Başkanı Onayında',
    KOB_READY: 'Kurul Başkanı Onayında',
    KOB_REVIEW: 'Kurul Başkanı Onayı Sürecinde',
    CHAIR_APPROVAL: 'Başkan Onayı Bekliyor',
    PUBLISHED: 'Yayımlandı',
    KILITLI: 'Kilitli',
    RETURNED: 'İade Edildi',
    ARCHIVED: 'Arşivlendi',
    NO_CONTENT: 'Bu Hafta Veri Yok'
  };

  const SPK_DEPARTMENTS = [
    'Aracılık Faaliyetleri Dairesi Başkanlığı',
    'Bağımsız Denetim ve Değerleme Faaliyetleri Dairesi Başkanlığı',
    'Denetleme Dairesi Başkanlığı',
    'Finansal Teknolojiler Dairesi Başkanlığı',
    'Katılım Finansmanı Dairesi Başkanlığı',
    'Ortaklıklar Finansmanı Dairesi Başkanlığı',
    'Piyasa Gözetim ve Denetim Dairesi Başkanlığı',
    'Uluslararası İlişkiler ve Sürdürülebilirlik Dairesi Başkanlığı',
    'Yatırım Fonları Dairesi Başkanlığı',
    'Yatırım Ortaklıkları Dairesi Başkanlığı',
    'Hukuk İşleri Dairesi Başkanlığı',
    'Strateji Geliştirme Dairesi Başkanlığı',
    'Bilgi Sistemleri Dairesi Başkanlığı',
    'Destek Hizmetleri Dairesi Başkanlığı',
    'İnsan Kaynakları ve Eğitim Dairesi Başkanlığı',
    'Kurumsal İletişim Dairesi Başkanlığı'
  ];

  const SPK_DEPARTMENT_ABBR = [
    'AFD', 'BDD', 'DEDA', 'FTD', 'KFD', 'OFD', 'PGD',
    'UİSD', 'YFD', 'YODA', 'HİD', 'SGD', 'BSD', 'DHD', 'İKED', 'KİD'
  ];

const BULLETIN_HEADING_GROUPS = [
    {
      code: 'A',
      title: 'İzahname / İhraç Belgesi Onaylanan Sermaye Piyasası Araçları',
      children: [
        ['A01', 'Ilk Halka Arzlar'],
        ['A02', 'Halka Açık Ortaklıkların Pay İhraçları'],
        ['A03', 'Diğer Ortaklıkların Pay İhraçları'],
        ['A04', 'Borçlanma Araçları İhracı'],
        ['A05', 'Diğer Sermaye Piyasası Araçları İhracı'],
        ['A06', 'Emeklilik Yatırım Fonu Payları İhracı']
      ]
    },
    {
      code: 'B',
      title: 'Yeni Faaliyet İzinleri',
      children: [
        ['B01', 'Yetki Belgesi Alınması'],
        ['B02', 'Yatırım Kuruluşlarının Yetkilendirilmesi'],
        ['B03', 'Yatırım Fonu Kuruluşları'],
        ['B04', 'Emeklilik Yatırım Fonu Kuruluşları'],
        ['B05', 'Borsa Yatırım Fonu Kuruluşu ve Halka Arzları'],
        ['B06', 'Girişim Sermayesi Yatırım Fonu Kuruluşları'],
        ['B07', 'Gayrimenkul Yatırım Fonu Kuruluşları'],
        ['B08', 'Bağımsız Denetim Kuruluşlarının Yetkilendirilmesi'],
        ['B09', 'Değerleme Şirketlerinin Yetkilendirilmesi'],
        ['B10', 'Derecelendirme Kuruluşlarının Yetkilendirilmesi'],
        ['B11', 'Gayrimenkul Dışı Varlık Değerleme Yetkili Kuruluşları'],
        ['B12', 'Makine ve Ekipman Değerleme Yetkili Kuruluşları'],
        ['B13', 'Varlık Kiralama Şirketi Kuruluşları'],
        ['B14', 'Kripto Varlık Hizmet Sağlayıcı Kuruluşu'],
        ['B15', 'Diğer Faaliyet İzinleri']
      ]
    },
    {
      code: 'C',
      title: 'Suç Duyurusu, İdari Para Cezası ile Diğer Yaptırım ve Tedbirler',
      children: [
        ['C01', 'Suç Duyuruları'],
        ['C02', 'İdari Para Cezaları'],
        ['C03', 'İşlem Yasakları'],
        ['C04', 'Lisans ve Yetki Belgesi İptalleri'],
        ['C05', 'Diğer Yaptırım ve Tedbirler']
      ]
    },
    {
      code: 'D',
      title: 'Sermaye Piyasası Kurumlarının Diğer Başvuru Sonuçları',
      children: [
        ['D01', 'Aracı Kurum Kuruluşu'],
        ['D02', 'Portföy Yönetim Şirketi Kuruluşları'],
        ['D03', 'Emeklilik Fonları Dönüşüm / İçtüzük / İzahname Değişikliği'],
        ['D04', 'Yatırım Fonlarının Devirleri'],
        ['D05', 'Yatırım Fonlarının Birleşme İşlemleri ve İzahname Değişikliği'],
        ['D06', 'Yatırım Fonlarının Dönüşüm ve İzahname Değişikliği'],
        ['D07', 'Yatırım Fonlarının Katılma Payı İhracı / İzahname ve İhraç Belgesi Onayı'],
        ['D08', 'Yatırım Fonlarının Tasfiyesi'],
        ['D09', 'İşletme Adı ve Unvan Değişiklikleri'],
        ['D10', 'Kendi İsteğiyle Listeden Çıkan Değerleme Şirketleri'],
        ['D11', 'Kendi İsteğiyle Listeden Çıkan Derecelendirme Şirketleri'],
        ['D12', 'Kendi İsteğiyle Yetkisi İptal Edilen Bağımsız Denetim Kuruluşları'],
        ['D13', 'Portföy Yönetim Şirketlerinin Sermaye Artırımları'],
        ['D14', 'Yatırım Kuruluşlarının Merkez Dışı Örgüt Açma Başvuruları'],
        ['D15', 'Yatırım Kuruluşlarının Sermaye Artırımları'],
        ['D16', 'Yatırım Ortaklıkları Sermaye Artırımları'],
        ['D17', 'Yetkilendirilen Platformlar Listesinden Çıkarılan Kitle Fonlaması Platformu'],
        ['D18', 'Emeklilik Yatırım Fonu Payları İhracı'],
        ['D19', 'Diğer Başvurular']
      ]
    },
    {
      code: 'E',
      title: 'Halka Açık Ortaklıkların Diğer Başvuru Sonuçları',
      children: [
        ['E01', 'Halka Açık Şirket Sermaye Artırım ve Azaltımları'],
        ['E02', 'Halka Açık Şirket Esas Sözleşme Değişiklikleri'],
        ['E03', 'Kayıtlı Sermaye Sistemine Geçişler'],
        ['E04', 'Halka Açık Şirket Kurul Kaydından Çıkış İşlemleri'],
        ['E05', 'Halka Açık Şirket Pay Alım Teklifleri'],
        ['E06', 'Halka Açık Şirket Birleşme ve Bölünme İşlemleri']
      ]
    },
    {
      code: 'F',
      title: 'Sermaye Piyasası Kurumlarının Ortaklık Yapısı Değişiklikleri',
      children: [
        ['F01', 'Aracı Kurumların Ortaklık Yapısı Değişiklikleri'],
        ['F02', 'Portföy Yönetim Şirketlerinin Ortaklık Yapısı Değişiklikleri'],
        ['F03', 'Yatırım Ortaklıkları Ortaklık Yapısı Değişiklikleri'],
        ['F04', 'Kitle Fonlama Platformları Ortaklık Yapısı Değişiklikleri']
      ]
    },
    {
      code: 'G',
      title: 'Duyuru ve İlke Kararları',
      children: [
        ['G01', 'İlke Kararları'],
        ['G02', 'Duyurular']
      ]
    },
    {
      code: 'H',
      title: 'Diğer Özel Durumlar',
      children: [
        ['H01', 'Borsada İşlem Görmeyen Ortaklıkların Özel Durum Açıklamaları']
      ]
    }
  ];

  const KBY_SLOTS = [
    { id: 'u-kby-empty', fullName: 'Boş KBY Kadrosu', title: 'Başkan Yardımcısı', isVacant: true },
    { id: 'u-kby-1', fullName: 'Uğur YAYLAÖNÜ', title: 'Başkan Yardımcısı', isVacant: false },
    { id: 'u-kby-2', fullName: 'Ali ERDURMUŞ', title: 'Başkan Yardımcısı', isVacant: false },
    { id: 'u-kby-3', fullName: 'Ender KURTULAN', title: 'Başkan Yardımcısı', isVacant: false },
    { id: 'u-kby-4', fullName: 'Aytaç DİKMEN', title: 'Başkan Yardımcısı', isVacant: false }
  ];

  const OFFICIAL_DEPARTMENT_CHAIRS = {
    'dep-1': { fullName: 'Aşkın ALICI', title: 'Daire Başkanı' },
    'dep-2': { fullName: 'Müge ÇETİN', title: 'Daire Başkanı (V.)' },
    'dep-3': { fullName: 'Gökhan NARİN', title: 'Daire Başkanı' },
    'dep-5': { fullName: 'Mustafa EKEN', title: 'Daire Başkanı (V.)' },
    'dep-6': { fullName: 'Kürşad Sait BABUÇCU', title: 'Daire Başkanı' },
    'dep-7': { fullName: 'Ercan URKAN', title: 'Daire Başkanı' },
    'dep-8': { fullName: 'Doç. Dr. M. Aslı KÜÇÜKGÜNGÖR', title: 'Daire Başkanı (V.)' },
    'dep-9': { fullName: 'Müge KARAKURUM', title: 'Daire Başkanı' },
    'dep-10': { fullName: 'Evrim CAN UZER', title: 'Daire Başkanı (V.)' },
    'dep-11': { fullName: 'Hatice Ebru TÖREMİŞ', title: 'Daire Başkanı' },
    'dep-12': { fullName: 'Doç. Dr. Alaattin ECER', title: 'Daire Başkanı' },
    'dep-13': { fullName: 'Yalçın AY', title: 'Daire Başkanı' },
    'dep-14': { fullName: 'Gürkan KÜÇÜKGÜNGÖR', title: 'Daire Başkanı' },
    'dep-15': { fullName: 'Efe Murat ERBAŞ', title: 'Daire Başkanı' },
    'dep-16': { fullName: 'Murat BİRİNCİ', title: 'Daire Başkanı' }
  };

  const Store = {
    load() {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        const seeded = seedState();
        this.save(seeded);
        return seeded;
      }
      try {
        return JSON.parse(raw);
      } catch (error) {
        console.error(error);
        const seeded = seedState();
        this.save(seeded);
        return seeded;
      }
    },
    save(nextState) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
    }
  };

  let state = ensureBaselineState(Store.load());
  let activeUserId = state.activeUserId || 'u-admin';
  if (!state.users.some((item) => item.id === activeUserId && item.isActive)) {
    activeUserId = 'u-admin';
    state.activeUserId = activeUserId;
    Store.save(state);
  }
  let currentView = 'dashboard';
  let selectedBulletinId = state.bulletins[0]?.id || null;
  let selectedSectionId = null;
  let selectedEntryId = null;
  let dragSubState = null;
  let dragGroupState = null;
  let previewAllSections = false;
  let pendingMergeTable = null;
  let dashboardYearFilter = 'all';
  let logFilterBulletin = 'all';
  let logFilterCategory = 'all';

  const app = document.getElementById('app');
  const activeDeptSelect = document.getElementById('active-dept');
  const activeUserSelect = document.getElementById('active-user');

  function seedState() {
    const now = isoNow();
    const users = [
      user('u-admin', 'Sistem Yöneticisi', 'Admin', 'ADMIN', null),
      user('u-kb', 'Mahmut SÜTCÜ', 'Kurul Başkanı', 'KB', null),
      user('u-kob', 'Kurul Özel Bürosu', 'Koordinasyon', 'KOB', null),
      user('u-kob-personel-1', 'KÖB Personeli', 'Personel', 'KOB_PERSONELI', null),
      ...KBY_SLOTS.map((slot) => user(slot.id, slot.fullName, slot.title, 'KBY', null, { isActive: !slot.isVacant, isVacant: slot.isVacant })),
      ...SPK_DEPARTMENTS.flatMap((_, index) => {
        const n = index + 1;
        const abbr = SPK_DEPARTMENT_ABBR[index];
        const depId = `dep-${n}`;
        return [
          user(`u-db-${n}`, `${abbr} Daire Başkanı`, 'Daire Başkanı', 'DB', depId),
          user(`u-dby-${n}`, `${abbr} Daire Başkan Yardımcısı`, 'Daire Başkan Yrd.', 'DBY', depId),
        ];
      })
    ];

    const departments = SPK_DEPARTMENTS.map((name, index) => {
      const id = `dep-${index + 1}`;
      const directChairApproval = id === 'dep-11';
      return {
        id,
        abbreviation: SPK_DEPARTMENT_ABBR[index] || '',
        officialName: name,
        displayName: departmentDisplayName(name),
        status: 'ACTIVE',
        isRequiredForWeeklyBulletin: true,
        reportsToType: directChairApproval ? 'KB' : 'KBY',
        reportsToUserId: directChairApproval ? 'u-kb' : KBY_SLOTS[(index % KBY_SLOTS.length)].id,
        responsibleKbyUserIds: directChairApproval ? [] : [KBY_SLOTS[(index % KBY_SLOTS.length)].id],
        directChairApproval,
        displayOrder: index + 1,
        sourceUrl: 'https://spk.gov.tr/hakkimizda/organizasyon/teskilat/daire-baskanliklari',
        validFrom: now,
        validTo: null
      };
    });

    return {
      activeUserId: 'u-admin',
      users,
      departments,
      bulletins: [],
      sections: [],
      approvals: [],
      logs: [],
      archives: [],
      headingGroups: BULLETIN_HEADING_GROUPS,
      createdAt: now
    };
  }

  function user(id, fullName, title, roleCode, departmentId, options = {}) {
    return {
      id,
      fullName,
      title,
      roleCode,
      departmentId,
      isActive: options.isActive !== undefined ? options.isActive : true,
      isVacant: Boolean(options.isVacant)
    };
  }

  function stripAcademicTitle(fullName) {
    return String(fullName || '')
      .replace(/^\s*(Prof\.?\s*Dr\.?|Yrd\.?\s*Do(?:c|\u00e7)\.?\s*Dr\.?|Do(?:c|\u00e7)\.?\s*Dr\.?|Dr\.?\s*(?:Ogr|\u00d6\u011fr)\.?\s*(?:Uyesi|\u00dcyesi)|Dr\.?|Ar(?:s|\u015f)\.?\s*G(?:o|\u00f6)r\.?|(?:O|\u00d6)(?:g|\u011f)r\.?\s*G(?:o|\u00f6)r\.?)\s+/i, '')
      .replace(/^\s*(Prof\.?|Yrd\.?\s*Do(?:c|\u00e7)\.?|Do(?:c|\u00e7)\.?|Dr\.?)\s+/i, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function officialChairName(chair) {
    return stripAcademicTitle(chair && chair.fullName ? chair.fullName : '');
  }

  function ensureBaselineState(nextState) {
    let changed = false;
    nextState.users = nextState.users || [];
    nextState.departments = nextState.departments || [];
    nextState.bulletins = nextState.bulletins || [];
    nextState.sections = nextState.sections || [];
    nextState.approvals = nextState.approvals || [];
    nextState.logs = nextState.logs || [];
    nextState.archives = nextState.archives || [];
    nextState.organizationSnapshots = nextState.organizationSnapshots || [];
    nextState.headingGroups = (nextState.headingGroups && nextState.headingGroups.length)
      ? nextState.headingGroups
      : BULLETIN_HEADING_GROUPS;

    const requiredCoreUsers = [
      { id: 'u-admin', fullName: 'Sistem Yöneticisi', title: 'Admin', roleCode: 'ADMIN', departmentId: null, isActive: true },
      { id: 'u-kb', fullName: 'Mahmut SÜTCÜ', title: 'Kurul Başkanı', roleCode: 'KB', departmentId: null, isActive: true },
      { id: 'u-kob', fullName: 'Kurul Özel Bürosu', title: 'Koordinasyon', roleCode: 'KOB', departmentId: null, isActive: true }
    ];

    requiredCoreUsers.forEach((requiredUser) => {
      let existing = nextState.users.find((item) => item.id === requiredUser.id);
      if (!existing) {
        existing = user(requiredUser.id, requiredUser.fullName, requiredUser.title, requiredUser.roleCode, requiredUser.departmentId, { isActive: requiredUser.isActive });
        nextState.users.push(existing);
        changed = true;
      } else {
        existing.fullName = requiredUser.fullName;
        existing.title = requiredUser.title;
        existing.roleCode = requiredUser.roleCode;
        existing.departmentId = requiredUser.departmentId;
        existing.isActive = true;
        existing.isVacant = false;
      }
    });

    KBY_SLOTS.forEach((slot) => {
      let existing = nextState.users.find((item) => item.id === slot.id);
      if (!existing) {
        existing = user(slot.id, slot.fullName, slot.title, 'KBY', null, { isActive: !slot.isVacant, isVacant: slot.isVacant });
        nextState.users.push(existing);
        changed = true;
      } else {
        existing.roleCode = 'KBY';
        existing.title = existing.title || slot.title;
        if (!slot.isVacant) {
          existing.fullName = slot.fullName;
          existing.title = slot.title;
          existing.isVacant = false;
          existing.isActive = true;
        } else if (!existing.fullName || existing.fullName === 'Bos KBY Kadrosu' || existing.fullName === 'Boş KBY Kadrosu') {
          existing.fullName = slot.fullName;
          existing.title = slot.title;
          existing.isVacant = true;
          existing.isActive = false;
        }
      }
    });

    if (!nextState.users.some((item) => item.id === 'u-kob-personel-1')) {
      nextState.users.push(user('u-kob-personel-1', 'KÖB Personeli', 'Personel', 'KOB_PERSONELI', null));
      changed = true;
    }
    nextState.users = nextState.users.filter((u) => u.roleCode !== 'UZMAN' && u.roleCode !== 'BURO_PERSONELI');

    SPK_DEPARTMENTS.forEach((_, index) => {
      const n = index + 1;
      const abbr = SPK_DEPARTMENT_ABBR[index];
      const depId = `dep-${n}`;
      const roleUsers = [
        { id: `u-dby-${n}`, fullName: `${abbr} Daire Başkan Yardımcısı`, title: 'Daire Başkan Yrd.', roleCode: 'DBY' }
      ];
      roleUsers.forEach(({ id, fullName, title, roleCode }) => {
        if (!nextState.users.some((u) => u.id === id)) {
          nextState.users.push(user(id, fullName, title, roleCode, depId));
          changed = true;
        }
      });
    });

    SPK_DEPARTMENTS.forEach((name, index) => {
      const id = `dep-${index + 1}`;
      const existingDepartment = nextState.departments.find((department) => department.id === id);
      if (existingDepartment) {
        existingDepartment.officialName = name;
        existingDepartment.displayName = departmentDisplayName(name);
        existingDepartment.abbreviation = SPK_DEPARTMENT_ABBR[index] || existingDepartment.abbreviation || '';
        existingDepartment.status = existingDepartment.status || 'ACTIVE';
        existingDepartment.isRequiredForWeeklyBulletin = true;
        if (existingDepartment.displayOrder == null) existingDepartment.displayOrder = index + 1;
        changed = true;
      } else {
        const directChairApproval = id === 'dep-11';
        const kbyId = KBY_SLOTS[index % KBY_SLOTS.length].id;
        nextState.departments.push({
          id,
          abbreviation: SPK_DEPARTMENT_ABBR[index] || '',
          officialName: name,
          displayName: departmentDisplayName(name),
          status: 'ACTIVE',
          isRequiredForWeeklyBulletin: true,
          reportsToType: directChairApproval ? 'KB' : 'KBY',
          reportsToUserId: directChairApproval ? 'u-kb' : kbyId,
          responsibleKbyUserIds: directChairApproval ? [] : [kbyId],
          directChairApproval,
          displayOrder: index + 1,
          sourceUrl: 'https://spk.gov.tr/hakkimizda/organizasyon/teskilat/daire-baskanliklari',
          validFrom: isoNow(),
          validTo: null
        });
        changed = true;
      }
    });

    Object.entries(OFFICIAL_DEPARTMENT_CHAIRS).forEach(([departmentId, chair]) => {
      const fullName = officialChairName(chair);
      let existingDb = nextState.users.find((item) => item.departmentId === departmentId && item.roleCode === 'DB');
      if (!existingDb) {
        existingDb = user(`u-db-${departmentId}`, fullName, chair.title, 'DB', departmentId, { isActive: true });
        nextState.users.push(existingDb);
        changed = true;
      } else {
        existingDb.fullName = fullName;
        existingDb.title = chair.title;
        existingDb.roleCode = 'DB';
        existingDb.departmentId = departmentId;
        existingDb.isActive = true;
        existingDb.isVacant = false;
      }
    });

    if (ensureOpenBulletinsHaveAllDepartments(nextState)) changed = true;
    nextState.sections.forEach((section) => {
      if (!Array.isArray(section.entries)) {
        section.entries = [{
          id: uid('entry'), order: 1,
          contentHtml: section.contentHtml || '',
          structuredTables: section.structuredTables ? [...section.structuredTables] : [],
          tables: section.tables ? [...section.tables] : [],
          approvalStatus: 'DRAFT', createdBy: null, createdByRole: null,
          approvedBy: null, approvedAt: null
        }];
        changed = true;
      } else if (section.entries.length === 0) {
        section.entries.push({ id: uid('entry'), order: 1, contentHtml: '', structuredTables: [], tables: [],
          approvalStatus: 'DRAFT', createdBy: null, createdByRole: null, approvedBy: null, approvedAt: null });
        changed = true;
      }
      section.entries.forEach((entry) => {
        if (!entry.approvalStatus) {
          entry.approvalStatus = 'DRAFT';
          entry.createdBy = entry.createdBy || null;
          entry.createdByRole = entry.createdByRole || null;
          entry.approvedBy = entry.approvedBy || null;
          entry.approvedAt = entry.approvedAt || null;
          changed = true;
        }
      });
    });
    if (nextState.departments.length < SPK_DEPARTMENTS.length) changed = true;
    if (changed) Store.save(nextState);
    return nextState;
  }

  function ensureOpenBulletinsHaveAllDepartments(targetState) {
    let changed = false;
    const activeDepartments = targetState.departments
      .filter((department) => department.status !== 'PASSIVE')
      .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
    targetState.bulletins
      .filter((bulletin) => bulletin.status !== 'PUBLISHED')
      .forEach((bulletin) => {
        const existingSections = targetState.sections.filter((section) => section.bulletinId === bulletin.id);
        const maxOrder = existingSections.reduce((max, section) => Math.max(max, section.order || 0), 0);
        let added = 0;
        activeDepartments.forEach((department) => {
          const exists = existingSections.some((section) => section.departmentId === department.id);
          if (exists) return;
          added += 1;
          targetState.sections.push(makeDepartmentSectionForBulletin(bulletin.id, department, maxOrder + added, targetState));
          changed = true;
        });
      });
    return changed;
  }

  function makeDepartmentSectionForBulletin(bulletinId, department, order, sourceState = state) {
    return {
      id: uid('section'),
      bulletinId,
      departmentId: department.id,
      departmentName: department.displayName,
      departmentOfficialName: department.officialName,
      responsibleKbyUserId: department.directChairApproval ? null : department.reportsToUserId,
      responsibleKbyName: department.directChairApproval ? null : userNameFromState(sourceState, department.reportsToUserId),
      responsibleKbyTitle: department.directChairApproval ? null : 'Başkan Yardımcısı',
      directChairApproval: department.directChairApproval,
      headingGroupCode: '',
      headingSubGroupCode: '',
      title: department.displayName,
      order,
      contentHtml: '',
      tables: [],
      structuredTables: [],
      attachments: [],
      status: 'SECTION_PREP',
      preparedBy: null,
      lastEditedBy: null,
      reviewedByDby: null,
      reviewedByDbyAt: null,
      approvedByDb: null,
      approvedByDbAt: null,
      submittedToKbyAt: null,
      approvedByKby: null,
      approvedByKbyAt: null,
      kobSuggestions: [],
      rejectionReason: null,
      version: 1,
      entries: []
    };
  }

  function departmentDisplayName(officialName) {
    return officialName.replace(' Dairesi Başkanlığı', ' Dairesi').replace(' Dairesi Başkanlığı', ' Dairesi');
  }

  function persist() {
    state.activeUserId = activeUserId;
    Store.save(state);
  }

  function uid(prefix) {
    return `${prefix}-${Math.random().toString(36).slice(2, 9)}-${Date.now().toString(36)}`;
  }

  function isoNow() {
    return new Date().toISOString();
  }

  function activeUser() {
    return state.users.find((item) => item.id === activeUserId) || state.users[0];
  }

  function isAdmin() {
    return activeUser().roleCode === 'ADMIN';
  }

  function canManageBulletin() {
    return ['ADMIN', 'KBY', 'KOB'].includes(activeUser().roleCode);
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function addLog(actionType, details) {
    state.logs.unshift({
      id: uid('log'),
      bulletinId: details?.bulletinId || null,
      sectionId: details?.sectionId || null,
      entryId: details?.entryId || null,
      actorUserId: activeUser().id,
      actorName: activeUser().fullName,
      actorRole: activeUser().roleCode,
      actionType,
      fieldName: details?.fieldName || null,
      oldValueSummary: details?.oldValueSummary || null,
      newValueSummary: details?.newValueSummary || null,
      reason: details?.reason || null,
      createdAt: isoNow(),
      versionBefore: details?.versionBefore || null,
      versionAfter: details?.versionAfter || null,
      oldContent: details?.oldContent || null,
      newContent: details?.newContent || null
    });
  }

  function boot() {
    renderUserSwitcher();
    bindTabs();
    bindGlobalActions();
    render();
  }

  function bindGlobalActions() {
    app.addEventListener('click', (event) => {
      if (event.defaultPrevented) return;
      const editButton = event.target.closest('[data-edit-user]');
      if (editButton) {
        event.preventDefault();
        event.stopPropagation();
        if (!isAdmin()) {
          alert('Bu işlem sadece admin kullanıcı tarafından yapılabilir.');
          return;
        }
        selectUserForEditing(editButton.dataset.editUser);
        return;
      }

      const createButton = event.target.closest('[data-create-user-role]');
      if (createButton) {
        event.preventDefault();
        event.stopPropagation();
        if (!isAdmin()) {
          alert('Bu işlem sadece admin kullanıcı tarafından yapılabilir.');
          return;
        }
        const roleCode = createButton.dataset.createUserRole;
        const departmentId = createButton.dataset.createUserDepartment || null;
        const item = createEditableUser(roleCode, departmentId);
        render();
        setTimeout(() => selectUserForEditing(item.id), 0);
      }
    });
  }

  function fillUserOptions(deptId) {
    const users = (deptId === 'system'
      ? state.users.filter((u) => u.isActive && !u.departmentId)
      : state.users.filter((u) => u.isActive && u.departmentId === deptId)
    ).filter((u) => u.roleCode !== 'KOB_PERSONELI');
    activeUserSelect.innerHTML = users
      .sort((a, b) => roleSort(a.roleCode) - roleSort(b.roleCode) || a.fullName.localeCompare(b.fullName, 'tr'))
      .map((u) => `<option value="${u.id}">${ROLE_SWITCHER_LABELS[u.roleCode] || `${ROLE_LABELS[u.roleCode]} — ${escapeHtml(u.fullName)}`}</option>`)
      .join('');
  }

  function renderUserSwitcher() {
    const currentUser = state.users.find((u) => u.id === activeUserId);
    const currentDept = currentUser?.departmentId || 'system';

    const deptOpts = [];
    if (state.users.some((u) => u.isActive && !u.departmentId)) {
      deptOpts.push('<option value="system">Sistem</option>');
    }
    state.departments
      .filter((dep) => state.users.some((u) => u.isActive && u.departmentId === dep.id))
      .sort((a, b) => a.displayOrder - b.displayOrder)
      .forEach((dep) => {
        deptOpts.push(`<option value="${dep.id}">${dep.abbreviation} — ${dep.displayName}</option>`);
      });
    activeDeptSelect.innerHTML = deptOpts.join('');
    activeDeptSelect.value = currentDept;

    fillUserOptions(currentDept);
    activeUserSelect.value = activeUserId;

    activeDeptSelect.onchange = () => {
      fillUserOptions(activeDeptSelect.value);
      activeUserId = activeUserSelect.value;
      persist();
      render();
    };
    activeUserSelect.onchange = () => {
      activeUserId = activeUserSelect.value;
      persist();
      render();
    };
  }

  function roleSort(roleCode) {
    const order = ['ADMIN', 'KB', 'KOB', 'KBY', 'DB', 'DBY', 'KOB_PERSONELI'];
    const index = order.indexOf(roleCode);
    return index === -1 ? 99 : index;
  }

  function bindTabs() {
    document.querySelectorAll('.tab').forEach((button) => {
      button.addEventListener('click', () => {
        currentView = button.dataset.view;
        document.querySelectorAll('.tab').forEach((tab) => tab.classList.toggle('active', tab === button));
        render();
      });
    });
  }

  function render() {
    renderUserSwitcher();
    const views = {
      dashboard: renderDashboard,
      organization: renderOrganization,
      bulletins: renderBulletins,
      workspace: renderWorkspace,
      archive: renderArchive,
      logs: renderLogs
    };
    views[currentView]();
  }

  function contentStatsHtml() {
    const taggedEntries = [];
    state.bulletins.forEach((b) => {
      const year = b.year || '?';
      state.sections.filter((s) => s.bulletinId === b.id).forEach((s) => {
        (s.entries || []).forEach((e) => taggedEntries.push({ ...e, year }));
      });
    });
    if (!taggedEntries.length) return '';

    const years = [...new Set(taggedEntries.map((e) => e.year))].sort((a, b) => Number(b) - Number(a));
    const groupCodes = state.headingGroups.map((g) => g.code);

    const matrix = {};
    years.forEach((y) => { matrix[y] = {}; });
    taggedEntries.forEach((e) => {
      const g = e.headingGroupCode || '—';
      matrix[e.year][g] = (matrix[e.year][g] || 0) + 1;
    });

    const yearTotals = {};
    years.forEach((y) => {
      yearTotals[y] = Object.values(matrix[y]).reduce((s, n) => s + n, 0);
    });
    const groupTotals = {};
    groupCodes.forEach((g) => {
      groupTotals[g] = years.reduce((s, y) => s + (matrix[y][g] || 0), 0);
    });
    groupTotals['—'] = years.reduce((s, y) => s + (matrix[y]['—'] || 0), 0);

    const activeGroups = groupCodes.filter((g) => groupTotals[g] > 0);

    const matrixHtml = `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Yıl</th>
              ${activeGroups.map((g) => `<th title="${escapeHtml(state.headingGroups.find((h) => h.code === g)?.title || '')}">${g}</th>`).join('')}
              ${groupTotals['—'] > 0 ? '<th>—</th>' : ''}
              <th>Toplam</th>
            </tr>
          </thead>
          <tbody>
            ${years.map((y) => `
              <tr>
                <td><strong>${y}</strong></td>
                ${activeGroups.map((g) => `<td style="text-align:center">${matrix[y][g] || ''}</td>`).join('')}
                ${groupTotals['—'] > 0 ? `<td style="text-align:center">${matrix[y]['—'] || ''}</td>` : ''}
                <td style="text-align:center"><strong>${yearTotals[y]}</strong></td>
              </tr>`).join('')}
            <tr style="border-top:2px solid var(--border)">
              <td class="muted">Toplam</td>
              ${activeGroups.map((g) => `<td style="text-align:center"><strong>${groupTotals[g] || ''}</strong></td>`).join('')}
              ${groupTotals['—'] > 0 ? `<td style="text-align:center"><strong>${groupTotals['—']}</strong></td>` : ''}
              <td style="text-align:center"><strong>${taggedEntries.length}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    `;

    const filterYear = years.includes(dashboardYearFilter) ? dashboardYearFilter : 'all';
    const filteredEntries = filterYear === 'all' ? taggedEntries : taggedEntries.filter((e) => String(e.year) === String(filterYear));

    const yearSelectHtml = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <label for="dash-year-filter" style="margin:0;white-space:nowrap">Yıl filtresi:</label>
        <select id="dash-year-filter">
          <option value="all"${filterYear === 'all' ? ' selected' : ''}>Tüm yıllar</option>
          ${years.map((y) => `<option value="${y}"${String(filterYear) === String(y) ? ' selected' : ''}>${y}</option>`).join('')}
        </select>
      </div>
    `;

    const subCount = {};
    filteredEntries.forEach((e) => {
      if (e.headingSubGroupCode) subCount[e.headingSubGroupCode] = (subCount[e.headingSubGroupCode] || 0) + 1;
    });
    const topSubs = Object.entries(subCount).sort(([, a], [, b]) => b - a).slice(0, 10);
    const subHtml = topSubs.length ? `
      <div class="table-wrap">
        <table>
          <thead><tr><th>Alt Başlık</th><th>Başlık</th><th style="text-align:center">Kayıt</th></tr></thead>
          <tbody>
            ${topSubs.map(([code, cnt]) => {
              const grp = state.headingGroups.find((g) => g.code === code[0]);
              const sub = grp?.children.find(([c]) => c === code);
              return `<tr>
                <td>${escapeHtml(code)}</td>
                <td class="muted">${escapeHtml(sub ? sub[1] : '—')}</td>
                <td style="text-align:center"><strong>${cnt}</strong></td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    ` : '<p class="muted">Bu yıla ait alt başlık etiketi yok.</p>';

    const filtGroupTotals = {};
    groupCodes.forEach((g) => {
      filtGroupTotals[g] = filteredEntries.filter((e) => e.headingGroupCode === g).length;
    });
    const filtActiveGroups = groupCodes.filter((g) => filtGroupTotals[g] > 0);
    const totalTagged = filteredEntries.filter((e) => e.headingGroupCode).length;
    const filtBulletinCount = filterYear === 'all'
      ? (state.bulletins.length || 1)
      : (state.bulletins.filter((b) => String(b.year) === String(filterYear)).length || 1);

    const groupStatsHtml = filtActiveGroups.length ? `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Kod</th>
              <th>Ana Başlık</th>
              <th style="text-align:center">Kayıt</th>
              <th style="text-align:center">Pay</th>
              <th style="text-align:center">Ort./Bülten</th>
              ${filterYear === 'all' ? '<th style="text-align:center">En Aktif Yıl</th>' : ''}
            </tr>
          </thead>
          <tbody>
            ${filtActiveGroups
              .map((g) => {
                const grpDef = state.headingGroups.find((h) => h.code === g);
                const total = filtGroupTotals[g];
                const share = totalTagged ? Math.round(total / totalTagged * 100) : 0;
                const avgPerBulletin = (total / filtBulletinCount).toFixed(1);
                const bestYear = filterYear === 'all'
                  ? years.reduce((best, y) => (matrix[y][g] || 0) > (matrix[best][g] || 0) ? y : best, years[0])
                  : null;
                return { g, grpDef, total, share, avgPerBulletin, bestYear };
              })
              .sort((a, b) => b.total - a.total)
              .map(({ g, grpDef, total, share, avgPerBulletin, bestYear }) => `
                <tr>
                  <td><strong>${g}</strong></td>
                  <td>${escapeHtml(grpDef?.title || g)}</td>
                  <td style="text-align:center">${total}</td>
                  <td style="text-align:center">
                    <div style="display:flex;align-items:center;gap:6px;justify-content:flex-end">
                      <div style="width:60px;height:6px;background:var(--border,#e5e7eb);border-radius:3px;overflow:hidden">
                        <div style="width:${share}%;height:100%;background:var(--accent,#2563eb);border-radius:3px"></div>
                      </div>
                      <span>%${share}</span>
                    </div>
                  </td>
                  <td style="text-align:center">${avgPerBulletin}</td>
                  ${filterYear === 'all' ? `<td style="text-align:center">${years.length > 1 ? bestYear : '—'}</td>` : ''}
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
    ` : '<p class="muted">Bu yıla ait başlık etiketi yok.</p>';

    return `
      <section class="panel">
        <h2>Başlık Grubu Dağılımı</h2>
        <p class="muted" style="margin-bottom:8px">Sütun başlıklarının üzerine gelerek grubu görebilirsiniz.</p>
        ${matrixHtml}
      </section>
      <section class="grid two">
        <div class="panel">
          <div class="toolbar" style="margin-bottom:0">
            <h2 style="margin:0">En Sık Kullanılan Alt Başlıklar</h2>
          </div>
          ${yearSelectHtml}
          ${subHtml}
        </div>
        <div class="panel">
          <h2>Ana Başlık İstatistikleri</h2>
          ${groupStatsHtml}
        </div>
      </section>
    `;
  }

  function bulletinYearStats() {
    const allBulletins = state.bulletins;
    if (!allBulletins.length) return null;

    const byYear = {};
    allBulletins.forEach((b) => {
      const y = b.year || '?';
      if (!byYear[y]) byYear[y] = { bulletins: [], sections: [], entries: [] };
      byYear[y].bulletins.push(b);
      const secs = state.sections.filter((s) => s.bulletinId === b.id);
      byYear[y].sections.push(...secs);
      secs.forEach((s) => byYear[y].entries.push(...(s.entries || [])));
    });

    return Object.entries(byYear)
      .sort(([a], [b]) => Number(b) - Number(a))
      .map(([year, data]) => {
        const total = data.bulletins.length;
        const publishedCount = data.bulletins.filter((b) => b.status === 'PUBLISHED').length;
        const entryCount = data.entries.length;
        const approvedEntries = data.entries.filter((e) => e.approvalStatus === 'APPROVED').length;
        const noContentSecs = data.sections.filter((s) => s.status === 'NO_CONTENT').length;
        const totalSecs = data.sections.length;
        const participationRate = totalSecs ? Math.round((totalSecs - noContentSecs) / totalSecs * 100) : 0;
        const avgEntries = publishedCount ? (entryCount / publishedCount).toFixed(1) : '—';
        const approvalRate = entryCount ? Math.round(approvedEntries / entryCount * 100) : 0;

        const deptEntryCount = {};
        data.sections.forEach((s) => {
          if (!s.departmentId) return;
          deptEntryCount[s.departmentId] = (deptEntryCount[s.departmentId] || 0) + (s.entries || []).length;
        });
        const topDeptId = Object.entries(deptEntryCount).sort(([, a], [, b]) => b - a)[0]?.[0];
        const topDept = topDeptId ? (state.departments.find((d) => d.id === topDeptId)?.abbreviation || topDeptId) : '—';

        return { year, total, publishedCount, entryCount, avgEntries, approvalRate, noContentSecs, participationRate, topDept };
      });
  }

  function renderDashboard() {
    const openBulletins = state.bulletins.filter((item) => item.status !== 'PUBLISHED').length;
    const published = state.bulletins.filter((item) => item.status === 'PUBLISHED').length;
    const pendingSections = state.sections.filter((item) => item.status !== 'PUBLISHED' && item.status !== 'KILITLI').length;
    const yearStats = bulletinYearStats();

    const yearStatsHtml = yearStats && yearStats.length ? `
      <section class="panel">
        <h2>Yıl Bazlı Özet İstatistikler</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Yıl</th>
                <th>Bülten</th>
                <th>Yayımlanan</th>
                <th>Toplam Kayıt</th>
                <th>Ort. Kayıt/Bülten</th>
                <th>Onay Oranı</th>
                <th>Katılım Oranı</th>
                <th>Veri Yok Bölüm</th>
                <th>En Aktif Daire</th>
              </tr>
            </thead>
            <tbody>
              ${yearStats.map((r) => `
                <tr>
                  <td><strong>${escapeHtml(String(r.year))}</strong></td>
                  <td style="text-align:center">${r.total}</td>
                  <td style="text-align:center">${r.publishedCount}</td>
                  <td style="text-align:center">${r.entryCount}</td>
                  <td style="text-align:center">${r.avgEntries}</td>
                  <td style="text-align:center">${r.entryCount ? `%${r.approvalRate}` : '—'}</td>
                  <td style="text-align:center">${r.participationRate ? `%${r.participationRate}` : '—'}</td>
                  <td style="text-align:center">${r.noContentSecs}</td>
                  <td style="text-align:center">${escapeHtml(r.topDept)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </section>
    ` : '';

    app.innerHTML = `
      <section class="grid three">
        ${metric('Aktif bülten', openBulletins)}
        ${metric('Yayımlanan', published)}
        ${metric('Açık bölüm', pendingSections)}
      </section>
      ${yearStatsHtml}
      ${contentStatsHtml()}
      <section class="grid two">
        <div class="panel">
          <h2>Faz 1 odağı</h2>
          <p class="muted">Bu prototip tarayıcının yerel depolaması üzerinde çalışır. Arayüz veriye doğrudan erişmez; tüm erişim tek veri bağdaştırıcısı üzerinden yürür.</p>
          <div class="cards">
            <div class="card"><strong>1.</strong> Admin organizasyon şeması ve kullanıcı tanımları.</div>
            <div class="card"><strong>2.</strong> Haftalık bülten açılışı ve organizasyon anlık kaydı.</div>
            <div class="card"><strong>3.</strong> Daire Başkan Yrd., Daire Başkanı, Başkan Yardımcısı, Kurul Özel Bürosu, Kurul Başkanı onay zinciri.</div>
            <div class="card"><strong>4.</strong> İşlem kayıtlı arşiv ve temiz/kayıtlı görünüm.</div>
          </div>
        </div>
        <div class="panel">
          <h2>Aktif kullanıcı yetkisi</h2>
          <p><strong>${escapeHtml(activeUser().fullName)}</strong></p>
          <p><span class="badge">${ROLE_LABELS[activeUser().roleCode]}</span></p>
          <p class="muted">Test için üstteki kullanıcı seçiminden farklı rollere geçilebilir.</p>
        </div>
      </section>
    `;
    document.getElementById('dash-year-filter')?.addEventListener('change', (e) => {
      dashboardYearFilter = e.target.value;
      render();
    });
  }

  function metric(label, value) {
    return `<div class="panel"><h2>${value}</h2><p class="muted">${label}</p></div>`;
  }

  function renderOrganization() {
    app.innerHTML = `
      <section class="panel">
        <div class="toolbar">
          <div>
            <h2>Organizasyon Şeması</h2>
            <p class="muted">Daire kartlarını KB veya KBY kolonlarına sürükleyerek bağlantı belirlenir. Bu ekran sadece admin tarafından değiştirilebilir.</p>
          </div>
          <div class="actions">
            <button ${isAdmin() ? '' : 'disabled'} id="sync-official-db-btn">SPK DB adlarını getir</button>
            <button ${isAdmin() ? '' : 'disabled'} id="add-user-btn">Kullanıcı ekle</button>
            <button ${isAdmin() ? '' : 'disabled'} id="import-personnel-btn">Personel toplu aktar</button>
            <button ${isAdmin() ? '' : 'disabled'} id="reset-demo-btn" class="danger">Demo veriyi sıfırla</button>
          </div>
        </div>
        ${organizationHierarchy()}
      </section>
      <section class="grid two">
        <div class="panel">
          <h2>Daire Bağlantıları</h2>
          <div class="table-wrap">${departmentTable()}</div>
        </div>
        <div class="panel" id="user-edit-panel">
          <h2>Kullanıcı ve unvan girişi</h2>
          ${userForm()}
        </div>
      </section>
      <section class="panel" id="personnel-import-panel" style="display:none;">
        <h2>Personel toplu aktarımı</h2>
        <p class="muted">CSV/TSV veya Excel'den kopyalanmış tablo kabul edilir. Kolonlar: Personel Adı Soyadı, Dairesi, Rol Grubu.</p>
        <div class="field">
          <label>CSV/Excel metni</label>
          <textarea id="personnel-import-text" class="editor" placeholder="Personel Adı Soyadı\tDairesi\tRol Grubu"></textarea>
        </div>
        <div class="actions" style="margin-top:12px">
          <button class="primary" id="run-personnel-import-btn">Aktar</button>
        </div>
      </section>
    `;

    bindOrganizationEvents();
  }

  function organizationHierarchy() {
    const kb = state.users.find((item) => item.roleCode === 'KB');
    const kob = state.users.find((item) => item.roleCode === 'KOB');
    const kbyUsers = KBY_SLOTS
      .map((slot) => state.users.find((item) => item.id === slot.id))
      .filter(Boolean);
    return `
      <div class="hierarchy">
        <div class="hierarchy-top">
          ${personNode(kb, 'Kurul Başkanı')}
          ${personNode(kob, 'Kurul Özel Bürosu (KÖB)')}
        </div>
        <div class="hierarchy-lanes">
          ${hierarchyLane('KB', kb?.id || 'u-kb', 'Doğrudan Kurul Başkanı')}
          ${kbyUsers.map((person, index) => hierarchyLane('KBY', person.id, `KBY ${index + 1}: ${person.fullName}`, person)).join('')}
        </div>
      </div>
    `;
  }

  function personNode(person, fallbackTitle) {
    return `
      <div class="hierarchy-node">
        <h3>${escapeHtml(fallbackTitle)}</h3>
        <p><strong>${escapeHtml(person?.fullName || fallbackTitle)}</strong></p>
        <p class="muted">${escapeHtml(person?.title || '')}</p>
        ${person && isAdmin() ? editUserButton(person.id, 'Düzenle') : ''}
      </div>
    `;
  }

  function hierarchyLane(type, userId, title, person) {
    const departments = state.departments
      .filter((department) => {
        if (type === 'KB') return department.reportsToType === 'KB';
        return department.reportsToType === 'KBY' && department.reportsToUserId === userId;
      })
      .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
    return `
      <div class="hierarchy-lane" data-assignment-type="${type}" data-assignment-user-id="${userId}" data-lane-id="${type}-${userId}">
        <h3>${escapeHtml(title)}${person?.isVacant ? ' <span class="badge warn">Boş</span>' : ''}</h3>
        ${person && isAdmin() ? editUserButton(person.id, 'Kişiyi düzenle') : ''}
        ${departments.map((department) => departmentHierarchyCard(department)).join('') || '<p class="muted">Bağlı daire yok</p>'}
      </div>
    `;
  }

  function departmentHierarchyCard(department) {
    const dbUsers = usersForDepartment(department.id, 'DB');
    const dbyUsers = usersForDepartment(department.id, 'DBY');
    const dbUser = dbUsers[0];
    return `
      <div class="department-card" data-department-id="${department.id}"${isAdmin() ? ' draggable="true"' : ''}>
        ${isAdmin() ? '<span class="drag-handle dept-drag-handle" title="Sırala">⠿</span>' : ''}
        <h4>${escapeHtml(department.displayName)}</h4>
        <p class="department-chief-line">
          <strong>Daire Başkanı:</strong> ${escapeHtml(dbUser?.fullName || 'Tanımlanmadı')}
          ${dbUser && isAdmin() ? editUserButton(dbUser.id, 'Düzenle') : ''}
          ${!dbUser && isAdmin() ? createUserButton('DB', department.id, 'DB ekle') : ''}
        </p>
        <div class="person-list">
          ${roleGroupRow('DBY', dbyUsers, department.id, 'DBY')}
        </div>
      </div>
    `;
  }

  function roleGroupRow(label, people, departmentId, roleCode) {
    const count = people.length;
    const names = people.slice(0, 3).map((person) => person.fullName).join(', ');
    const suffix = count > 3 ? ` +${count - 3}` : '';
    return `
      <div class="person-row editable">
        <span>${escapeHtml(label)}: ${count} kişi${names ? ` (${escapeHtml(names)}${suffix})` : ''}</span>
        ${isAdmin() ? `<button type="button" data-create-user-role="${roleCode}" data-create-user-department="${departmentId}" onclick="window.HaftalikBultenApp.createUser('${roleCode}', '${departmentId}'); return false;">Ekle</button>` : ''}
      </div>
    `;
  }

  function editablePersonRow(person, prefix = '') {
    return `
      <div class="person-row editable">
        <span>${prefix ? `${escapeHtml(prefix)}: ` : ''}${escapeHtml(person.fullName)} - ${escapeHtml(person.title)}</span>
        ${isAdmin() ? editUserButton(person.id, 'Düzenle') : ''}
      </div>
    `;
  }

  function emptyRoleRow(departmentId, roleCode, label) {
    return `
      <div class="person-row editable">
        <span>${escapeHtml(label)}</span>
        ${isAdmin() ? createUserButton(roleCode, departmentId, 'Ekle') : ''}
      </div>
    `;
  }

  function addRoleRow(departmentId, roleCode, label) {
    return `
      <div class="person-row editable">
        <span>${escapeHtml(label)}</span>
        ${createUserButton(roleCode, departmentId, 'Ekle')}
      </div>
    `;
  }

  function editUserButton(userId, label) {
    return `<button type="button" data-edit-user="${userId}" onclick="window.HaftalikBultenApp.editUser('${userId}'); return false;">${escapeHtml(label)}</button>`;
  }

  function createUserButton(roleCode, departmentId, label) {
    return `<button type="button" data-create-user-role="${roleCode}" data-create-user-department="${departmentId || ''}" onclick="window.HaftalikBultenApp.createUser('${roleCode}', '${departmentId || ''}'); return false;">${escapeHtml(label)}</button>`;
  }

  function usersForDepartment(departmentId, roleCode) {
    return state.users.filter((item) => item.departmentId === departmentId && item.roleCode === roleCode);
  }

  function departmentTable() {
    const sorted = [...state.departments].sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
    return `
      <table>
        <thead><tr>${isAdmin() ? '<th></th>' : ''}<th>Daire</th><th>Bagli oldugu</th><th>Zorunlu</th><th>Admin baglanti</th></tr></thead>
        <tbody>
          ${sorted.map((department) => `
            <tr data-dept-row="${department.id}"${isAdmin() ? ' draggable="true"' : ''}>
              ${isAdmin() ? `<td class="dept-row-handle" title="Sırala">⠿</td>` : ''}
              <td>${escapeHtml(department.displayName)}</td>
              <td>${department.reportsToType === 'KB' ? 'Doğrudan Kurul Başkanı' : escapeHtml(userName(department.reportsToUserId))}</td>
              <td>${department.isRequiredForWeeklyBulletin ? '<span class="badge ok">Evet</span>' : '<span class="badge">Opsiyonel</span>'}</td>
              <td>${departmentAssignmentSelect(department)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  function departmentAssignmentSelect(department) {
    const value = department.reportsToType === 'KB' ? 'KB:u-kb' : `KBY:${department.reportsToUserId}`;
    return `
      <select class="department-assignment-select" data-department-id="${department.id}" ${isAdmin() ? '' : 'disabled'}>
        <option value="KB:u-kb" ${value === 'KB:u-kb' ? 'selected' : ''}>Doğrudan Kurul Başkanı</option>
        ${state.users.filter((item) => item.roleCode === 'KBY').map((item) => {
          const optionValue = `KBY:${item.id}`;
          return `<option value="${optionValue}" ${value === optionValue ? 'selected' : ''}>${escapeHtml(item.fullName)}</option>`;
        }).join('')}
      </select>
    `;
  }

  function userForm() {
    return `
      <div class="form-grid">
        <div class="field">
          <label>Kullanıcı</label>
          <select id="edit-user-id">
            ${state.users.map((item) => `<option value="${item.id}">${escapeHtml(item.fullName)} - ${ROLE_LABELS[item.roleCode]}</option>`).join('')}
          </select>
        </div>
        <div class="field">
          <label>Rol</label>
          <select id="edit-user-role" ${isAdmin() ? '' : 'disabled'}>
            ${Object.keys(ROLE_LABELS).map((role) => `<option value="${role}">${ROLE_LABELS[role]}</option>`).join('')}
          </select>
        </div>
        <div class="field">
          <label>Ad Soyad</label>
          <input id="edit-user-name" ${isAdmin() ? '' : 'disabled'}>
        </div>
        <div class="field">
          <label>Unvan</label>
          <input id="edit-user-title" ${isAdmin() ? '' : 'disabled'}>
        </div>
        <div class="field wide">
          <label>Daire</label>
          <select id="edit-user-department" ${isAdmin() ? '' : 'disabled'}>
            <option value="">Yok</option>
            ${state.departments.map((dep) => `<option value="${dep.id}">${escapeHtml(dep.displayName)}</option>`).join('')}
          </select>
        </div>
        <div class="wide actions">
          <button class="primary" id="save-user-btn" ${isAdmin() ? '' : 'disabled'}>Kullanıcı kaydet</button>
        </div>
      </div>
    `;
  }

  function bindOrganizationEvents() {
    const editUserId = document.getElementById('edit-user-id');
    if (editUserId) {
      const loadSelectedUser = () => {
        const item = state.users.find((userItem) => userItem.id === editUserId.value);
        document.getElementById('edit-user-role').value = item.roleCode;
        document.getElementById('edit-user-name').value = item.fullName;
        document.getElementById('edit-user-title').value = item.title;
        document.getElementById('edit-user-department').value = item.departmentId || '';
      };
      editUserId.onchange = loadSelectedUser;
      loadSelectedUser();
    }

    document.getElementById('save-user-btn')?.addEventListener('click', () => {
      if (!isAdmin()) return;
      const item = state.users.find((userItem) => userItem.id === editUserId.value);
      if (!item) return;
      const before = `${item.fullName} / ${item.title} / ${item.roleCode}`;
      item.roleCode = document.getElementById('edit-user-role').value;
      item.fullName = document.getElementById('edit-user-name').value.trim();
      item.title = document.getElementById('edit-user-title').value.trim();
      item.departmentId = document.getElementById('edit-user-department').value || null;
      item.isVacant = false;
      item.isActive = true;

      addLog('USER_UPDATED', { oldValueSummary: before, newValueSummary: `${item.fullName} / ${item.title} / ${item.roleCode}` });
      persist();
      render();
      alert('Kullanıcı kaydedildi.');
    });

    document.getElementById('add-user-btn')?.addEventListener('click', () => {
      if (!isAdmin()) return;
      const item = createEditableUser('DBY', state.departments[0]?.id || null);
      render();
      setTimeout(() => selectUserForEditing(item.id), 0);
    });

    document.getElementById('sync-official-db-btn')?.addEventListener('click', () => {
      if (!isAdmin()) return;
      applyOfficialDepartmentChairs();
      addLog('OFFICIAL_DEPARTMENT_CHAIRS_SYNCED', { newValueSummary: 'SPK daire başkanı adları uygulandı' });
      persist();
      render();
      alert('SPK daire başkanı adları ilgili dairelere işlendi.');
    });

    document.getElementById('import-personnel-btn')?.addEventListener('click', () => {
      if (!isAdmin()) return;
      const panel = document.getElementById('personnel-import-panel');
      if (!panel) return;
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    document.getElementById('run-personnel-import-btn')?.addEventListener('click', () => {
      if (!isAdmin()) return;
      const text = document.getElementById('personnel-import-text')?.value || '';
      const result = importPersonnelText(text);
      persist();
      render();
      alert(`${result.created} yeni, ${result.updated} güncellenen, ${result.skipped} atlanan kayıt.`);
    });

    document.getElementById('reset-demo-btn')?.addEventListener('click', () => {
      if (!isAdmin()) return;
      if (!confirm('Tüm haftalık bülten demo verisi sıfırlansın mı?')) return;
      state = seedState();
      activeUserId = 'u-admin';
      selectedBulletinId = null;
      selectedSectionId = null;
      persist();
      render();
    });

    document.querySelectorAll('.department-assignment-select').forEach((select) => {
      select.addEventListener('change', () => {
        if (!isAdmin()) return;
        const [targetRole, targetUserId] = select.value.split(':');
        moveDepartment(select.dataset.departmentId, targetRole, targetUserId);
      });
    });

    if (isAdmin()) {
      let dragDeptId = null;

      document.querySelectorAll('.department-card[draggable]').forEach((el) => {
        el.addEventListener('dragstart', (e) => {
          dragDeptId = el.dataset.departmentId;
          el.classList.add('dragging');
          e.dataTransfer.effectAllowed = 'move';
          e.stopPropagation();
        });
        el.addEventListener('dragend', () => {
          el.classList.remove('dragging');
          document.querySelectorAll('.department-card').forEach((c) => c.classList.remove('drag-over-dept'));
          dragDeptId = null;
        });
        el.addEventListener('dragover', (e) => {
          if (!dragDeptId || dragDeptId === el.dataset.departmentId) return;
          e.preventDefault();
          e.stopPropagation();
          document.querySelectorAll('.department-card').forEach((c) => c.classList.remove('drag-over-dept'));
          el.classList.add('drag-over-dept');
        });
        el.addEventListener('dragleave', (e) => {
          if (!el.contains(e.relatedTarget)) el.classList.remove('drag-over-dept');
        });
        el.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          el.classList.remove('drag-over-dept');
          if (!dragDeptId || dragDeptId === el.dataset.departmentId) return;
          reorderDepartment(dragDeptId, el.dataset.departmentId);
        });
      });

      document.querySelectorAll('.hierarchy-lane').forEach((lane) => {
        lane.addEventListener('dragover', (e) => {
          if (!dragDeptId) return;
          e.preventDefault();
        });
        lane.addEventListener('drop', (e) => {
          if (!dragDeptId) return;
          e.preventDefault();
          reorderDepartment(dragDeptId, null, lane);
        });
      });

      let dragRowId = null;
      document.querySelectorAll('tr[data-dept-row]').forEach((row) => {
        row.addEventListener('dragstart', (e) => {
          dragRowId = row.dataset.deptRow;
          row.classList.add('dragging');
          e.dataTransfer.effectAllowed = 'move';
        });
        row.addEventListener('dragend', () => {
          row.classList.remove('dragging');
          document.querySelectorAll('tr[data-dept-row]').forEach((r) => r.classList.remove('drag-over-dept'));
          dragRowId = null;
        });
        row.addEventListener('dragover', (e) => {
          if (!dragRowId || dragRowId === row.dataset.deptRow) return;
          e.preventDefault();
          document.querySelectorAll('tr[data-dept-row]').forEach((r) => r.classList.remove('drag-over-dept'));
          row.classList.add('drag-over-dept');
        });
        row.addEventListener('dragleave', (e) => {
          if (!row.contains(e.relatedTarget)) row.classList.remove('drag-over-dept');
        });
        row.addEventListener('drop', (e) => {
          e.preventDefault();
          row.classList.remove('drag-over-dept');
          if (!dragRowId || dragRowId === row.dataset.deptRow) return;
          reorderDepartment(dragRowId, row.dataset.deptRow);
        });
      });
    }

  }

  function reorderDepartment(draggedId, beforeId, lane) {
    const fromIdx = state.departments.findIndex((d) => d.id === draggedId);
    if (fromIdx === -1) return;
    const [moved] = state.departments.splice(fromIdx, 1);
    if (beforeId) {
      const toIdx = state.departments.findIndex((d) => d.id === beforeId);
      state.departments.splice(toIdx === -1 ? state.departments.length : toIdx, 0, moved);
    } else if (lane) {
      const laneType = lane.dataset.assignmentType;
      const laneUserId = lane.dataset.assignmentUserId;
      const lastInLane = [...state.departments].reverse().find((d) =>
        laneType === 'KB' ? d.reportsToType === 'KB' : d.reportsToType === 'KBY' && d.reportsToUserId === laneUserId
      );
      const insertAt = lastInLane ? state.departments.findIndex((d) => d.id === lastInLane.id) + 1 : state.departments.length;
      state.departments.splice(insertAt, 0, moved);
    } else {
      state.departments.push(moved);
    }
    state.departments.forEach((d, i) => { d.displayOrder = i + 1; });
    persist();
    render();
  }

  function moveDepartment(departmentId, targetRole, targetUserId) {
    const department = state.departments.find((item) => item.id === departmentId);
    if (!department) return;
    const before = `${department.displayName}: ${department.reportsToType} / ${department.reportsToUserId || ''}`;
    department.reportsToType = targetRole;
    department.directChairApproval = targetRole === 'KB';
    if (targetRole === 'KB') {
      department.reportsToUserId = 'u-kb';
      department.responsibleKbyUserIds = [];
    } else {
      const kby = state.users.find((item) => item.id === targetUserId && item.roleCode === 'KBY')
        || state.users.find((item) => item.roleCode === 'KBY')
        || state.users.find((item) => item.id === 'u-kby-1');
      department.reportsToUserId = kby.id;
      department.responsibleKbyUserIds = [kby.id];
    }
    addLog('ORG_DEPARTMENT_MOVED', {
      oldValueSummary: before,
      newValueSummary: `${department.displayName}: ${department.reportsToType} / ${department.reportsToUserId}`,
      reason: 'Organizasyon güncellemesi'
    });
    persist();
    render();
  }

  function selectUserForEditing(userId) {
    const select = document.getElementById('edit-user-id');
    if (!select) return;
    if (![...select.options].some((option) => option.value === userId)) {
      const item = state.users.find((userItem) => userItem.id === userId);
      if (!item) return;
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = `${item.fullName} - ${ROLE_LABELS[item.roleCode]}`;
      select.appendChild(option);
    }
    select.value = userId;
    select.dispatchEvent(new Event('change'));
    const panel = document.getElementById('user-edit-panel') || select.closest('.panel');
    panel?.classList.add('edit-panel-highlight');
    panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => panel?.classList.remove('edit-panel-highlight'), 1400);
    document.getElementById('edit-user-name')?.focus();
  }

  function createEditableUser(roleCode, departmentId) {
    const id = uid('u');
    const item = user(id, 'Yeni Kullanıcı', ROLE_LABELS[roleCode] || 'Unvan', roleCode, departmentId);
    state.users.push(item);
    syncOrganizationNodeForUser(item);
    addLog('USER_CREATED', { newValueSummary: `${item.fullName} / ${ROLE_LABELS[roleCode]}` });
    persist();
    return item;
  }

  function applyOfficialDepartmentChairs() {
    Object.entries(OFFICIAL_DEPARTMENT_CHAIRS).forEach(([departmentId, chair]) => {
      const fullName = officialChairName(chair);
      let existingDb = state.users.find((item) => item.departmentId === departmentId && item.roleCode === 'DB');
      if (!existingDb) {
        existingDb = user(`u-db-${departmentId}`, fullName, chair.title, 'DB', departmentId, { isActive: true });
        state.users.push(existingDb);
      } else {
        existingDb.fullName = fullName;
        existingDb.title = chair.title;
        existingDb.roleCode = 'DB';
        existingDb.departmentId = departmentId;
        existingDb.isActive = true;
        existingDb.isVacant = false;
      }

    });
  }

  function importPersonnelText(text) {
    const result = { created: 0, updated: 0, skipped: 0 };
    const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (!lines.length) return result;
    const rows = lines.map(parsePersonnelLine);
    const first = rows[0].map(normalizeText);
    const hasHeader = first.some((cell) => cell.includes('personel')) && first.some((cell) => cell.includes('daire'));
    const dataRows = hasHeader ? rows.slice(1) : rows;
    dataRows.forEach((columns) => {
      const fullName = (columns[0] || '').trim();
      const departmentText = (columns[1] || '').trim();
      const roleText = (columns[2] || '').trim();
      const department = findDepartmentByText(departmentText);
      const roleCode = normalizeRoleGroup(roleText);
      const departmentId = department?.id || (isKobDepartmentText(departmentText) ? 'kob' : null);
      if (!fullName || !departmentId || !roleCode) {
        result.skipped += 1;
        return;
      }
      let existing = state.users.find((item) => normalizeText(item.fullName) === normalizeText(fullName));
      if (!existing) {
        existing = user(uid('u'), fullName, ROLE_LABELS[roleCode], roleCode, departmentId, { isActive: true });
        state.users.push(existing);
        result.created += 1;
      } else {
        existing.fullName = fullName;
        existing.title = ROLE_LABELS[roleCode];
        existing.roleCode = roleCode;
        existing.departmentId = departmentId;
        existing.isActive = true;
        existing.isVacant = false;
        result.updated += 1;
      }

    });
    addLog('PERSONNEL_BULK_IMPORTED', { newValueSummary: `${result.created} yeni, ${result.updated} güncelleme, ${result.skipped} atlanan` });
    return result;
  }

  function parsePersonnelLine(line) {
    if (line.includes('\t')) return line.split('\t');
    if (line.includes(';')) return line.split(';');
    return line.split(',');
  }

  function normalizeRoleGroup(value) {
    const normalized = normalizeText(value);
    if (normalized.includes('dby') || normalized.includes('daire baskan yardimcisi')) return 'DBY';
    if (normalized.includes('db') || normalized.includes('daire baskani')) return 'DB';
    return null;
  }

  function findDepartmentByText(value) {
    const normalized = normalizeText(value);
    return state.departments.find((department) => {
      const official = normalizeText(department.officialName);
      const display = normalizeText(department.displayName);
      return official === normalized || display === normalized || official.includes(normalized) || normalized.includes(display);
    });
  }

  function isKobDepartmentText(value) {
    const normalized = normalizeText(value);
    return normalized.includes('kurul ozel burosu') || normalized === 'kob';
  }

  function normalizeText(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/ı/g, 'i')
      .replace(/ğ/g, 'g')
      .replace(/ü/g, 'u')
      .replace(/ş/g, 's')
      .replace(/ö/g, 'o')
      .replace(/ç/g, 'c')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function renderBulletins() {
    app.innerHTML = `
      <section class="panel">
        <div class="toolbar">
          <div>
            <h2>Haftalık bültenler</h2>
            <p class="muted">Yeni bülten açıldığında mevcut organizasyon snapshot olarak saklanır.</p>
          </div>
          ${canManageBulletin() ? '<button class="primary" id="new-bulletin-btn">Yeni hafta bülteni</button>' : ''}
        </div>
        <div class="table-wrap">${bulletinTable()}</div>
      </section>
      <section class="panel">
        <h2>Organizasyon kaydı Önizleme</h2>
        ${selectedBulletinId ? snapshotPreview(selectedBulletinId) : '<p class="muted">Bülten seçin.</p>'}
      </section>
      <section class="panel">
        <div class="toolbar">
          <div>
            <h2>Başlık gruplandırma şablonu</h2>
            <p class="muted">Bülten maddeleri anlam/ailesi bazında bu kodlara bağlanır.</p>
          </div>
          ${isAdmin() ? '<button class="primary" id="add-group-btn">+ Yeni Grup</button>' : ''}
        </div>
        <div id="heading-admin-body">
          ${isAdmin() ? `<div class="heading-admin">${renderHeadingGroupAdmin()}</div>` : headingGroupReference()}
        </div>
      </section>
    `;
    document.getElementById('new-bulletin-btn')?.addEventListener('click', createBulletin);
    document.querySelectorAll('[data-select-bulletin]').forEach((button) => {
      button.addEventListener('click', () => {
        selectedBulletinId = button.dataset.selectBulletin;
        currentView = 'workspace';
        activateTab('workspace');
        render();
      });
    });
    document.querySelectorAll('[data-edit-bulletin]').forEach((button) => {
      button.addEventListener('click', () => editBulletin(button.dataset.editBulletin));
    });
    document.querySelectorAll('[data-delete-bulletin]').forEach((button) => {
      button.addEventListener('click', () => deleteBulletin(button.dataset.deleteBulletin));
    });
    if (isAdmin()) {
      document.getElementById('add-group-btn')?.addEventListener('click', () => {
        showHeadingGroupModal(null, (code, title) => {
          if (state.headingGroups.some((g) => g.code === code)) { alert('Bu kod zaten var.'); return; }
          state.headingGroups.push({ code, title, children: [] });
          persist();
          refreshHeadingAdmin();
        });
      });
      bindHeadingGroupAdmin();
    }
  }

  function deleteBulletin(bulletinId) {
    if (!isAdmin()) return;
    const bulletin = state.bulletins.find((b) => b.id === bulletinId);
    if (!bulletin || bulletin.status === 'PUBLISHED') return;
    const label = `${bulletin.year}/${bulletin.weekNumber} - ${bulletin.title}`;
    if (!confirm(`"${label}" bülteni ve tüm bölümleri kalıcı olarak silinecek. Onaylıyor musunuz?`)) return;
    state.bulletins = state.bulletins.filter((b) => b.id !== bulletinId);
    state.sections = state.sections.filter((s) => s.bulletinId !== bulletinId);
    state.logs = state.logs.filter((l) => l.bulletinId !== bulletinId);
    state.approvals = (state.approvals || []).filter((a) => a.bulletinId !== bulletinId);
    if (selectedBulletinId === bulletinId) selectedBulletinId = null;
    addLog('BULLETIN_DELETED', { bulletinId, newValueSummary: label });
    persist();
    render();
  }

  function bulletinTable() {
    if (!state.bulletins.length) return '<p class="muted">Henüz bülten yok.</p>';
    return `
      <table>
        <thead><tr><th>Hafta</th><th>Tarih</th><th>Başlık</th><th>Durum</th><th>Bölüm</th><th></th></tr></thead>
        <tbody>
          ${state.bulletins.map((bulletin) => {
            const sections = state.sections.filter((section) => section.bulletinId === bulletin.id);
            return `
              <tr>
                <td>${bulletin.year}/${bulletin.weekNumber}</td>
                <td>${escapeHtml(formatBulletinDate(bulletin))}</td>
                <td>${escapeHtml(bulletin.title)}</td>
                <td>${statusBadge(bulletin.status)}</td>
                <td>${sections.length}</td>
                <td class="actions">
                  <button data-select-bulletin="${bulletin.id}">Aç</button>
                  ${bulletin.status !== 'PUBLISHED' && canManageBulletin() ? `<button data-edit-bulletin="${bulletin.id}">Düzenle</button>` : ''}
                  ${bulletin.status !== 'PUBLISHED' && isAdmin() ? `<button class="danger" data-delete-bulletin="${bulletin.id}">Sil</button>` : ''}
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  function headingGroupReference() {
    return `
      <div class="heading-reference">
        ${state.headingGroups.map((group) => `
          <details>
            <summary><strong>${escapeHtml(group.code)}</strong> ${escapeHtml(group.title)}</summary>
            <div class="code-list">
              ${group.children.map(([code, title], i) => `<span><strong>${escapeHtml(subGroupDisplayCode(group, i))}</strong> ${escapeHtml(title)}</span>`).join('')}
            </div>
          </details>
        `).join('')}
      </div>
    `;
  }

  function headingGroupOptions(selectedCode) {
    return [
      '<option value="">Başlık ailesi seçilmedi</option>',
      ...state.headingGroups.map((group) => (
        `<option value="${group.code}" ${group.code === selectedCode ? 'selected' : ''}>${escapeHtml(group.code)} - ${escapeHtml(group.title)}</option>`
      ))
    ].join('');
  }

  function headingSubGroupOptions(groupCode, selectedCode) {
    const group = state.headingGroups.find((item) => item.code === groupCode);
    if (!group) return '<option value="">Önce ana aile seçin</option>';
    return [
      '<option value="">Alt aile seçilmedi</option>',
      ...group.children.map(([code, title], i) => (
        `<option value="${code}" ${code === selectedCode ? 'selected' : ''}>${escapeHtml(subGroupDisplayCode(group, i))} - ${escapeHtml(title)}</option>`
      ))
    ].join('');
  }

  function headingGroupLabel(section) {
    const group = state.headingGroups.find((item) => item.code === section.headingGroupCode);
    if (!group) return 'Başlık ailesi seçilmedi';
    const subIdx = group.children.findIndex(([code]) => code === section.headingSubGroupCode);
    const sub = subIdx !== -1 ? group.children[subIdx] : null;
    return sub ? `${group.code} / ${subGroupDisplayCode(group, subIdx)} - ${sub[1]}` : `${group.code} - ${group.title}`;
  }

  function subGroupDisplayCode(group, index) {
    const prefix = group.code.replace(/\d+$/, '');
    return prefix + String(index + 1).padStart(2, '0');
  }

  function nextSubGroupCode(group) {
    const prefix = group.code.replace(/\d+$/, '');
    const nums = group.children
      .map(([c]) => c)
      .filter((c) => c.startsWith(prefix))
      .map((c) => parseInt(c.slice(prefix.length), 10))
      .filter((n) => !isNaN(n));
    const max = nums.length ? Math.max(...nums) : 0;
    return prefix + String(max + 1).padStart(2, '0');
  }

  function renderHeadingGroupAdmin() {
    return state.headingGroups.map((group) => `
      <div class="group-card" data-group-code="${escapeHtml(group.code)}" draggable="true">
        <div class="group-header">
          <span class="drag-handle group-drag-handle" title="Sırala">⠿</span>
          <div class="group-header-info">
            <strong>${escapeHtml(group.code)}</strong>
            <span>${escapeHtml(group.title)}</span>
          </div>
          <div class="actions">
            <button class="add-subgroup-btn" data-group-code="${escapeHtml(group.code)}">+ Alt Grup</button>
            <button class="edit-group-btn" data-group-code="${escapeHtml(group.code)}">Düzenle</button>
          </div>
        </div>
        <div class="subgroup-list" data-drop-target="${escapeHtml(group.code)}">
          ${group.children.map(([code, title], idx) => `
            <div class="subgroup-item" draggable="true"
                 data-sub-code="${escapeHtml(code)}"
                 data-from-group="${escapeHtml(group.code)}">
              <span class="drag-handle">⠿</span>
              <span class="sub-code">${escapeHtml(subGroupDisplayCode(group, idx))}</span>
              <span class="sub-title">${escapeHtml(title)}</span>
              <div class="actions">
                <button class="edit-subgroup-btn"
                        data-sub-code="${escapeHtml(code)}"
                        data-group-code="${escapeHtml(group.code)}">Düzenle</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  function refreshHeadingAdmin() {
    const body = document.getElementById('heading-admin-body');
    if (!body) return;
    body.innerHTML = `<div class="heading-admin">${renderHeadingGroupAdmin()}</div>`;
    bindHeadingGroupAdmin();
  }

  function bindHeadingGroupAdmin() {
    document.querySelectorAll('.group-card').forEach((el) => {
      el.addEventListener('dragstart', (e) => {
        if (e.target.closest('.subgroup-item')) return;
        dragGroupState = el.dataset.groupCode;
        el.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      el.addEventListener('dragend', () => {
        el.classList.remove('dragging');
        document.querySelectorAll('.group-card').forEach((c) => c.classList.remove('drag-over-group'));
        dragGroupState = null;
      });
      el.addEventListener('dragover', (e) => {
        if (!dragGroupState || dragSubState || dragGroupState === el.dataset.groupCode) return;
        e.preventDefault();
        document.querySelectorAll('.group-card').forEach((c) => c.classList.remove('drag-over-group'));
        el.classList.add('drag-over-group');
      });
      el.addEventListener('drop', (e) => {
        el.classList.remove('drag-over-group');
        if (!dragGroupState || dragSubState || dragGroupState === el.dataset.groupCode) return;
        e.preventDefault();
        e.stopPropagation();
        const fromIdx = state.headingGroups.findIndex((g) => g.code === dragGroupState);
        const toIdx = state.headingGroups.findIndex((g) => g.code === el.dataset.groupCode);
        if (fromIdx === -1 || toIdx === -1) return;
        const [moved] = state.headingGroups.splice(fromIdx, 1);
        state.headingGroups.splice(toIdx, 0, moved);
        dragGroupState = null;
        persist();
        refreshHeadingAdmin();
      });
    });

    function applySubDrop(toGroupCode, beforeCode) {
      if (!dragSubState) return;
      const fromGroup = state.headingGroups.find((g) => g.code === dragSubState.fromGroupCode);
      const toGroup = state.headingGroups.find((g) => g.code === toGroupCode);
      if (!fromGroup || !toGroup) return;
      const fromIdx = fromGroup.children.findIndex(([c]) => c === dragSubState.code);
      if (fromIdx === -1) return;
      const [sub] = fromGroup.children.splice(fromIdx, 1);
      if (beforeCode) {
        const toIdx = toGroup.children.findIndex(([c]) => c === beforeCode);
        toGroup.children.splice(toIdx === -1 ? toGroup.children.length : toIdx, 0, sub);
      } else {
        toGroup.children.push(sub);
      }
      dragSubState = null;
      persist();
      refreshHeadingAdmin();
    }

    document.querySelectorAll('.subgroup-item').forEach((el) => {
      el.addEventListener('dragstart', (e) => {
        e.stopPropagation();
        dragSubState = { code: el.dataset.subCode, fromGroupCode: el.dataset.fromGroup };
        el.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      el.addEventListener('dragend', () => el.classList.remove('dragging'));
      el.addEventListener('dragover', (e) => {
        if (!dragSubState || dragSubState.code === el.dataset.subCode) return;
        e.preventDefault();
        e.stopPropagation();
        document.querySelectorAll('.subgroup-item').forEach((i) => i.classList.remove('drag-over-item'));
        el.classList.add('drag-over-item');
      });
      el.addEventListener('dragleave', (e) => {
        if (!el.contains(e.relatedTarget)) el.classList.remove('drag-over-item');
      });
      el.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.classList.remove('drag-over-item');
        applySubDrop(el.dataset.fromGroup, el.dataset.subCode);
      });
    });

    document.querySelectorAll('.subgroup-list').forEach((zone) => {
      zone.addEventListener('dragover', (e) => {
        if (!dragSubState) return;
        e.preventDefault();
        zone.classList.add('drag-over');
      });
      zone.addEventListener('dragleave', (e) => {
        if (!zone.contains(e.relatedTarget)) zone.classList.remove('drag-over');
      });
      zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        applySubDrop(zone.dataset.dropTarget, null);
      });
    });

    document.querySelectorAll('.edit-group-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const groupCode = btn.dataset.groupCode;
        const group = state.headingGroups.find((g) => g.code === groupCode);
        if (!group) return;
        showHeadingGroupModal(group, (code, title) => {
          const conflict = state.headingGroups.some((g) => g.code === code && g.code !== groupCode);
          if (conflict) { alert('Bu kod başka bir grupta kullanılıyor.'); return; }
          group.code = code;
          group.title = title;
          persist();
          refreshHeadingAdmin();
        });
      });
    });

    document.querySelectorAll('.add-subgroup-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const groupCode = btn.dataset.groupCode;
        const group = state.headingGroups.find((g) => g.code === groupCode);
        if (!group) return;
        showSubGroupModal(null, nextSubGroupCode(group), (code, title) => {
          const allChildren = state.headingGroups.flatMap((g) => g.children);
          if (allChildren.some(([c]) => c === code)) { alert('Bu alt grup kodu zaten var.'); return; }
          group.children.push([code, title]);
          persist();
          refreshHeadingAdmin();
        });
      });
    });

    document.querySelectorAll('.edit-subgroup-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const subCode = btn.dataset.subCode;
        const groupCode = btn.dataset.groupCode;
        const group = state.headingGroups.find((g) => g.code === groupCode);
        if (!group) return;
        const sub = group.children.find(([c]) => c === subCode);
        if (!sub) return;
        showSubGroupModal(sub, null, (code, title) => {
          const conflict = state.headingGroups.flatMap((g) => g.children).some(([c]) => c === code && c !== subCode);
          if (conflict) { alert('Bu alt grup kodu başka bir yerde kullanılıyor.'); return; }
          sub[0] = code;
          sub[1] = title;
          persist();
          refreshHeadingAdmin();
        });
      });
    });
  }

  function showHeadingGroupModal(defaults, onSave) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>${defaults ? 'Grup Düzenle' : 'Yeni Grup'}</h3>
        <div class="field">
          <label>Kod (örn: H00)</label>
          <input type="text" id="hg-code" value="${escapeHtml(defaults ? defaults.code : '')}" placeholder="X00" maxlength="10">
        </div>
        <div class="field">
          <label>Başlık</label>
          <input type="text" id="hg-title" value="${escapeHtml(defaults ? defaults.title : '')}" placeholder="Grup adı">
        </div>
        <div class="modal-actions">
          <button id="hg-cancel">İptal</button>
          <button class="primary" id="hg-confirm">Kaydet</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    document.getElementById('hg-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    document.getElementById('hg-confirm').addEventListener('click', () => {
      const code = document.getElementById('hg-code').value.trim().toUpperCase();
      const title = document.getElementById('hg-title').value.trim();
      if (!code || !title) { alert('Kod ve başlık zorunludur.'); return; }
      close();
      onSave(code, title);
    });
    document.getElementById('hg-code').focus();
  }

  function showSubGroupModal(defaults, suggestedCode, onSave) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>${defaults ? 'Alt Grup Düzenle' : 'Yeni Alt Grup'}</h3>
        <div class="field">
          <label>Kod</label>
          <input type="text" id="sg-code" value="${escapeHtml(defaults ? defaults[0] : (suggestedCode || ''))}" placeholder="X00" maxlength="10">
        </div>
        <div class="field">
          <label>Başlık</label>
          <input type="text" id="sg-title" value="${escapeHtml(defaults ? defaults[1] : '')}" placeholder="Alt grup adı">
        </div>
        <div class="modal-actions">
          <button id="sg-cancel">İptal</button>
          <button class="primary" id="sg-confirm">Kaydet</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    document.getElementById('sg-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    document.getElementById('sg-confirm').addEventListener('click', () => {
      const code = document.getElementById('sg-code').value.trim().toUpperCase();
      const title = document.getElementById('sg-title').value.trim();
      if (!code || !title) { alert('Kod ve başlık zorunludur.'); return; }
      close();
      onSave(code, title);
    });
    document.getElementById('sg-code').focus();
  }

  function showBulletinModal(defaults, onSave) {
    const now = new Date();
    const year = defaults ? defaults.year : now.getFullYear();
    const weekNumber = defaults ? defaults.weekNumber : getWeekNumber(now);
    const title = defaults ? defaults.title : '';
    const todayIso = now.toISOString().slice(0, 10);
    const dateIso = defaults && defaults.bulletinDate ? defaults.bulletinDate : todayIso;
    const dateValue = dateIso ? dateIso.split('-').reverse().join('.') : '';

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>${defaults ? 'Bülten bilgilerini düzenle' : 'Yeni haftalık bülten'}</h3>
        <div class="form-grid">
          <div class="field">
            <label>Yıl</label>
            <input type="number" id="modal-year" min="2000" max="2099" value="${year}">
          </div>
          <div class="field">
            <label>Hafta no</label>
            <input type="number" id="modal-week" min="1" max="53" value="${weekNumber}">
          </div>
        </div>
        <div class="field">
          <label>Bülten tarihi</label>
          <input type="text" id="modal-date" value="${dateValue}" placeholder="gg.aa.yyyy" maxlength="10">
        </div>
        <div class="field">
          <label>Başlık</label>
          <input type="text" id="modal-title" value="${escapeHtml(title)}" placeholder="${year}/${weekNumber} Haftalık Bülten">
        </div>
        <div class="modal-actions">
          <button id="modal-cancel">İptal</button>
          <button class="primary" id="modal-confirm">Kaydet</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const yearInput = document.getElementById('modal-year');
    const weekInput = document.getElementById('modal-week');
    const titleInput = document.getElementById('modal-title');

    function updatePlaceholder() {
      titleInput.placeholder = `${yearInput.value}/${weekInput.value} Haftalık Bülten`;
    }
    yearInput.addEventListener('input', updatePlaceholder);
    weekInput.addEventListener('input', updatePlaceholder);

    function close() { overlay.remove(); }
    document.getElementById('modal-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

    document.getElementById('modal-confirm').addEventListener('click', () => {
      const y = Number(yearInput.value);
      const w = Number(weekInput.value);
      if (!y || !w || w < 1 || w > 53) {
        alert('Geçerli bir yıl ve hafta numarası girin.');
        return;
      }
      const t = titleInput.value.trim() || `${y}/${w} Haftalık Bülten`;
      const rawDate = document.getElementById('modal-date').value.trim();
      const dateParts = rawDate.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
      const d = dateParts ? `${dateParts[3]}-${dateParts[2]}-${dateParts[1]}` : '';
      close();
      onSave(y, w, t, d);
    });
  }

  function createBulletin() {
    if (!canManageBulletin()) return;
    showBulletinModal(null, (year, weekNumber, title, bulletinDate) => {
      const exists = state.bulletins.some((item) => item.year === year && item.weekNumber === weekNumber);
      if (exists) {
        alert('Bu yıl/hafta için bülten zaten var.');
        return;
      }
      const bulletinId = uid('bulletin');
      const snapshot = captureOrganizationSnapshot(bulletinId);
      const requiredDepartments = state.departments
        .filter((department) => department.status !== 'PASSIVE')
        .sort((a, b) => (a.displayOrder || 0) - (b.displayOrder || 0));
      const bulletin = {
        id: bulletinId,
        year,
        weekNumber,
        bulletinDate: bulletinDate || '',
        title,
        status: 'SECTION_PREP',
        createdBy: activeUser().id,
        createdAt: isoNow(),
        organizationSnapshotId: snapshot.id,
        submittedToChairAt: null,
        approvedByChairAt: null,
        publishedAt: null,
        archiveRecordId: null
      };
      state.bulletins.unshift(bulletin);
      requiredDepartments.forEach((department, index) => {
        state.sections.push(makeDepartmentSectionForBulletin(bulletinId, department, index + 1));
      });
      addLog('BULLETIN_CREATED', { bulletinId, newValueSummary: bulletin.title });
      addLog('ORGANIZATION_SNAPSHOT_CAPTURED', { bulletinId, newValueSummary: snapshot.id });
      selectedBulletinId = bulletinId;
      persist();
      currentView = 'workspace';
      activateTab('workspace');
      render();
    });
  }

  function editBulletin(bulletinId) {
    if (!canManageBulletin()) return;
    const bulletin = state.bulletins.find((item) => item.id === bulletinId);
    if (!bulletin || bulletin.status === 'PUBLISHED') return;
    showBulletinModal(bulletin, (year, weekNumber, title, bulletinDate) => {
      const conflict = state.bulletins.some((item) => item.id !== bulletinId && item.year === year && item.weekNumber === weekNumber);
      if (conflict) {
        alert('Bu yıl/hafta için başka bir bülten zaten var.');
        return;
      }
      addLog('BULLETIN_UPDATED', { bulletinId, oldValueSummary: bulletin.title, newValueSummary: title });
      bulletin.year = year;
      bulletin.weekNumber = weekNumber;
      bulletin.bulletinDate = bulletinDate || '';
      bulletin.title = title;
      persist();
      render();
    });
  }

  function captureOrganizationSnapshot(bulletinId) {
    const snapshot = {
      id: uid('snapshot'),
      bulletinId,
      capturedAt: isoNow(),
      chairUserId: 'u-kb',
      chairName: userName('u-kb'),
      kobReviewUserId: 'u-kob',
      kobReviewUserName: userName('u-kob'),
      kbyAssignments: state.departments
        .filter((department) => department.reportsToType === 'KBY')
        .map((department) => ({ departmentId: department.id, kbyUserId: department.reportsToUserId })),
      departmentAssignments: state.departments.map((department) => ({
        departmentId: department.id,
        reportsToType: department.reportsToType,
        reportsToUserId: department.reportsToUserId,
        directChairApproval: department.directChairApproval
      })),
      directChairDepartments: state.departments.filter((department) => department.directChairApproval).map((department) => department.id),
      sourceUrls: ['https://www.spk.gov.tr/hakkimizda/organizasyon/teskilat']
    };
    state.organizationSnapshots = state.organizationSnapshots || [];
    state.organizationSnapshots.push(snapshot);
    return snapshot;
  }

  function snapshotPreview(bulletinId) {
    const bulletin = state.bulletins.find((item) => item.id === bulletinId);
    const snapshot = state.organizationSnapshots?.find((item) => item.id === bulletin?.organizationSnapshotId);
    if (!snapshot) return '<p class="muted">Organizasyon kaydı bulunamadı.</p>';
    return `
      <p><strong>Organizasyon kaydı:</strong> ${snapshot.id}</p>
      <p><strong>Alınma zamanı:</strong> ${new Date(snapshot.capturedAt).toLocaleString('tr-TR')}</p>
      <p><strong>Doğrudan Kurul Başkanı daireleri:</strong> ${snapshot.directChairDepartments.length}</p>
      <p><strong>KBY atamaları:</strong> ${snapshot.kbyAssignments.length}</p>
    `;
  }

  function kobNoContentPanel(bulletin, allSections) {
    const deptSections = allSections.filter((s) => s.departmentId);
    if (!deptSections.length) return '';
    const rows = deptSections.map((section) => {
      const isNoContent = section.status === 'NO_CONTENT';
      const dept = state.departments.find((d) => d.id === section.departmentId);
      const abbr = dept ? dept.abbreviation : '';
      const badgeCls = isNoContent ? '' : 'ok';
      const badgeLabel = isNoContent ? 'Veri Yok' : STATUS_LABELS[section.status] || section.status;
      return `
        <tr>
          <td>${escapeHtml(abbr)}</td>
          <td>${escapeHtml(section.departmentName || section.title)}</td>
          <td><span class="badge ${badgeCls}">${badgeLabel}</span></td>
          <td>
            ${!isNoContent && ['SECTION_PREP', 'DBY_REVIEW', 'DB_APPROVAL'].includes(section.status)
              ? `<button class="danger" data-kob-no-content="${section.id}">Veri Yok İşaretle</button>`
              : ''}
            ${isNoContent
              ? `<button data-kob-revert-no-content="${section.id}">Geri Al</button>`
              : ''}
          </td>
        </tr>
      `;
    }).join('');
    return `
      <section class="panel">
        <h2>Daire Veri Durumu <span class="muted" style="font-weight:normal;font-size:0.85em">— KÖB toplu işlem</span></h2>
        <table style="width:100%;border-collapse:collapse">
          <thead><tr>
            <th style="text-align:left;padding:4px 8px">Kısa Ad</th>
            <th style="text-align:left;padding:4px 8px">Daire</th>
            <th style="text-align:left;padding:4px 8px">Durum</th>
            <th style="text-align:left;padding:4px 8px">İşlem</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </section>
    `;
  }

  function renderWorkspace() {
    const bulletin = selectedBulletinId
      ? state.bulletins.find((item) => item.id === selectedBulletinId)
      : state.bulletins[0];
    if (!bulletin) {
      app.innerHTML = `<section class="panel"><h2>Çalışma alanı</h2><p class="muted">Önce bir haftalık bülten oluşturun.</p></section>`;
      return;
    }
    selectedBulletinId = bulletin.id;
    const allSections = state.sections.filter((section) => section.bulletinId === bulletin.id).sort((a, b) => a.order - b.order);
    const userRole = activeUser().roleCode;
    const hideNoContent = ['KBY', 'KOB', 'KOB_PERSONELI', 'KB'].includes(userRole);
    const sections = allSections.filter((section) => {
      if (!canViewSection(section)) return false;
      if (hideNoContent && section.status === 'NO_CONTENT') return false;
      if (sectionHasData(section)) return true;
      if (canPerformSectionAction(section, 'MARK_NO_CONTENT')) return true;
      return activeUser().departmentId === section.departmentId;
    });
    selectedSectionId = selectedSectionId && sections.some((item) => item.id === selectedSectionId) ? selectedSectionId : (sections[0] && sections[0].id);
    const selectedSection = sections.find((section) => section.id === selectedSectionId);
    const sectionEntries = selectedSection ? (selectedSection.entries || []) : [];
    if (!selectedEntryId || !sectionEntries.some((e) => e.id === selectedEntryId)) {
      selectedEntryId = sectionEntries.length > 0 ? sectionEntries[0].id : null;
    }
    const selectedEntry = sectionEntries.find((e) => e.id === selectedEntryId) || null;
    const isKobOrAdmin = activeUser().roleCode === 'ADMIN';
    const isKb = activeUser().roleCode === 'KB';
    const effectiveShowAll = isKb || previewAllSections;
    const previewSections = effectiveShowAll ? sections : (selectedSection ? [selectedSection] : sections);
    const previewLabel = effectiveShowAll ? '' : (selectedSection ? ` — ${escapeHtml(selectedSection.title)}` : '');
    app.innerHTML = `
      <section class="panel">
        <div class="toolbar">
          <div>
            <h2>${escapeHtml(bulletin.title)}</h2>
            <p class="muted">${STATUS_LABELS[bulletin.status]} - Organizasyon kaydı: ${escapeHtml(bulletin.organizationSnapshotId)}</p>
          </div>
          <div class="actions">
            ${bulletin.status !== 'PUBLISHED' && canManageBulletin() ? `<button id="edit-bulletin-btn">Bülten bilgilerini düzenle</button>` : ''}
            <button id="publish-btn" class="primary" ${canChairApprove(bulletin) ? '' : 'disabled'}>Onayla ve yayımla</button>
          </div>
        </div>
      </section>
      ${isKobOrAdmin ? kobNoContentPanel(bulletin, allSections) : ''}
      <section class="grid two">
        <div class="panel">
          <h2>Bölümler</h2>
          <div class="cards">
            ${sections.length ? sections.map((section) => sectionCard(section)).join('') : '<p class="muted">Bu kullanıcının görebileceği bölüm yok.</p>'}
          </div>
        </div>
        <div class="panel">
          ${selectedSection ? sectionEditor(selectedSection, selectedEntry) : '<p class="muted">Bölüm yok.</p>'}
        </div>
      </section>
      <section class="panel">
        <div class="toolbar" style="margin-bottom:8px">
          <h2 style="margin:0">Bütünleşik önizleme${previewLabel}</h2>
          ${['KBY'].includes(activeUser().roleCode) && selectedSection && !previewAllSections
            ? '<button id="preview-show-all-btn">Tüm Daireleri Göster</button>'
            : ''}
        </div>
        ${bulletinPreview(bulletin.id, false, previewSections)}
      </section>
    `;
    bindWorkspaceEvents(bulletin, selectedSection, selectedEntry);
  }

  function sectionCard(section) {
    const entries = section.entries || [];
    const entryCount = entries.length;
    const approvedCount = entries.filter((e) => e.approvalStatus === 'APPROVED').length;
    const kobEntryComments = entries.reduce((sum, e) => sum + ((e.kobSuggestions || []).length), 0);
    const kobSectionComments = (section.kobSuggestions || []).length;
    const kobTotal = kobEntryComments + kobSectionComments;
    return `
      <div class="card${section.id === selectedSectionId ? ' card-selected' : ''}">
        <div class="toolbar">
          <div>
            <h3>${escapeHtml(section.title)}</h3>
            <p class="muted">${section.directChairApproval ? 'Doğrudan Kurul Başkanı' : escapeHtml(section.responsibleKbyName || 'Başkan Yardımcısı yok')}</p>
            <div class="section-stats">
              <span class="badge">${entryCount} kayıt</span>
              ${entryCount > 0 ? `<span class="badge ${approvedCount === entryCount ? 'ok' : 'warn'}">${approvedCount}/${entryCount} onaylı</span>` : ''}
              ${kobTotal > 0 ? `<span class="badge warn">KÖB: ${kobTotal} yorum</span>` : ''}
            </div>
            ${statusBadge(section.status)}
          </div>
          <div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end">
            <button data-section-id="${section.id}">Seç</button>
            ${canPerformSectionAction(section, 'MARK_NO_CONTENT') ? `<button class="danger" data-card-no-content="${section.id}">Veri Yok</button>` : ''}
            ${canPerformSectionAction(section, 'REVERT_NO_CONTENT') ? `<button data-card-revert-no-content="${section.id}">Veri Girişine Geri Al</button>` : ''}
          </div>
        </div>
      </div>
    `;
  }

  function sectionHasData(section) {
    if (section.status !== 'SECTION_PREP') return true;
    return (section.entries || []).some((entry) =>
      (entry.contentHtml || '').trim() ||
      (entry.structuredTables || []).length ||
      (entry.tables || []).length
    );
  }

  function sectionExcerpt(section) {
    const entries = section.entries || [];
    for (const entry of entries) {
      const text = String(entry.contentHtml || '').replace(/\s+/g, ' ').trim();
      if (text) return text.length > 180 ? `${text.slice(0, 180)}...` : text;
      if (entry.structuredTables && entry.structuredTables.length) return `${entry.structuredTables.length} tablo aktarıldı.`;
      if (entry.tables && entry.tables.length) return `${entry.tables.length} tablo satırı girildi.`;
    }
    return 'İçerik girilmedi.';
  }

  function sectionEditor(section, selectedEntry) {
    const canEditSec = canEditSection(section);
    const canEditCurrentEntry = selectedEntry ? canEditEntry(selectedEntry, section) : false;
    const entries = section.entries || [];
    const previewLabels = computePreviewLabels(section.bulletinId);

    let entryEditorHtml = '<p class="muted" style="margin:8px 0">Düzenlemek için bir kayıt seçin veya yeni kayıt ekleyin.</p>';
    if (selectedEntry) {
      const userEnteredTable = (selectedEntry.structuredTables || []).find((t) => t._userEntered);
      let tableTextValue;
      if (userEnteredTable && userEnteredTable._hasMerge) {
        pendingMergeTable = userEnteredTable;
        const totalCols = Math.max(...userEnteredTable.rows.map((r) => r.reduce((s, c) => s + (c.colspan || 1), 0)));
        tableTextValue = `[Birleşik tablo: ${userEnteredTable.rows.length} satır × ${totalCols} sütun — yeniden yapıştırarak değiştirin]`;
      } else {
        pendingMergeTable = null;
        tableTextValue = userEnteredTable
          ? userEnteredTable.rows.map((row) => row.join('\t')).join('\n')
          : tableToText(selectedEntry.tables);
      }
      const pdfTables = (selectedEntry.structuredTables || []).filter((t) => !t._userEntered);
      const entryGroup = selectedEntry.headingGroupCode || section.headingGroupCode || '';
      const entrySub = selectedEntry.headingSubGroupCode || section.headingSubGroupCode || '';
      entryEditorHtml = `
        <div class="form-grid" style="margin-bottom:8px">
          <div class="field">
            <label>Ana grup</label>
            <select id="entry-heading-group" ${canEditCurrentEntry ? '' : 'disabled'}>${headingGroupOptions(entryGroup)}</select>
          </div>
          <div class="field">
            <label>Alt grup</label>
            <select id="entry-heading-subgroup" ${canEditCurrentEntry ? '' : 'disabled'}>${headingSubGroupOptions(entryGroup, entrySub)}</select>
          </div>
        </div>
        <div class="field">
          <label>İçerik</label>
          <textarea id="section-content" class="editor" ${canEditCurrentEntry ? '' : 'disabled'}>${escapeHtml(selectedEntry.contentHtml)}</textarea>
        </div>
        <div class="field">
          <label>Tablo — Word/Excel'den yapıştırın veya elle yazın. İlk satır başlık olur. Tek kolon, çok kolon, pipe (|) veya tab ayraçlı format desteklenir. Birleşik hücre için HTML tabloyu (tarayıcıdan kopyala) yapıştırın.</label>
          <textarea id="section-table" ${canEditCurrentEntry ? '' : 'disabled'} placeholder="Excel hücrelerini buraya yapıştırın">${escapeHtml(tableTextValue)}</textarea>
        </div>
        <div id="merge-header-ctrl" style="display:${pendingMergeTable ? 'flex' : 'none'};align-items:center;gap:8px;margin-top:4px">
          <label style="margin:0;font-size:13px">Başlık satırı sayısı:</label>
          <input type="number" id="merge-header-rows" min="0" max="10" value="${pendingMergeTable ? pendingMergeTable.headerRows : 1}" style="width:56px">
        </div>
        <div id="table-preview" class="table-wrap" style="margin-top:8px"></div>
        ${pdfTables.length ? renderStructuredTables(pdfTables) : ''}
      `;
    }

    return `
      <h2>${escapeHtml(section.title)}</h2>
      <p>${statusBadge(section.status)} <span class="muted">v${section.version}</span></p>
      <div class="field">
        <label>Başlık</label>
        <input id="section-title" value="${escapeHtml(section.title)}" ${canEditSec ? '' : 'disabled'}>
      </div>
      <div class="form-grid">
        <div class="field">
          <label>Varsayılan ana grup <span class="muted">(yeni kayıtlara atanır)</span></label>
          <select id="section-heading-group" ${canEditSec ? '' : 'disabled'}>${headingGroupOptions(section.headingGroupCode || '')}</select>
        </div>
        <div class="field">
          <label>Varsayılan alt grup</label>
          <select id="section-heading-subgroup" ${canEditSec ? '' : 'disabled'}>${headingSubGroupOptions(section.headingGroupCode || '', section.headingSubGroupCode || '')}</select>
        </div>
      </div>
      <div style="margin:12px 0 6px"><strong>Kayıtlar</strong> <span class="muted">(${entries.length})</span></div>
      <div class="entry-list">
        ${entries.map((entry) => {
          const entryStatus = entry.approvalStatus || 'DRAFT';
          const entryEditable = canEditEntry(entry, section);
          const entryCanDelete = canDeleteEntry(entry, section);
          const entryCanApprove = canApproveEntry(entry);
          const entryCanRevoke = canRevokeEntry(entry);
          const canKobSuggest = ['KOB', 'KOB_PERSONELI', 'ADMIN'].includes(activeUser().roleCode) && section.status !== 'KILITLI';
          const statusLabel = ENTRY_STATUS_LABELS[entryStatus] || entryStatus;
          const badgeCls = entryStatus === 'APPROVED' ? 'ok' : entryStatus === 'PENDING' ? 'warn' : entryStatus === 'RETURNED' ? 'warn' : '';
          const entrySuggestions = entry.kobSuggestions || [];
          return `
            <div class="entry-item${entry.id === selectedEntry?.id ? ' active' : ''}">
              <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
                <span class="entry-label">${previewLabels.get(entry.id) || `Kayıt ${entry.order}`}</span>
                <span class="badge ${badgeCls}">${statusLabel}</span>
                ${(() => { const eg = entry.headingGroupCode || section.headingGroupCode; const es = entry.headingSubGroupCode || section.headingSubGroupCode; const grp = state.headingGroups.find((g) => g.code === eg); const sub = grp?.children.find(([c]) => c === es); return sub ? `<span class="muted" style="font-size:11px">${escapeHtml(sub[0])}</span>` : (eg ? `<span class="muted" style="font-size:11px">${escapeHtml(eg)}</span>` : ''); })()}
              </div>
              <div class="actions">
                <button data-select-entry="${entry.id}">${entryEditable ? 'Düzenle' : 'Görüntüle'}</button>
                ${entryCanDelete && entries.length > 1 ? `<button class="danger" data-delete-entry="${entry.id}">Sil</button>` : ''}
                <button data-toggle-kob-suggestions="${entry.id}">KÖB yorum/önerisi</button><span class="badge ${entrySuggestions.length ? 'ok' : ''}">${entrySuggestions.length ? `${entrySuggestions.length} yorum` : 'Yok'}</span>
              </div>
              <div id="kob-suggestions-${entry.id}" class="kob-entry-suggestions" style="display:none">
                ${entrySuggestions.map((s) => `
                  <div class="kob-suggestion-item">
                    <span class="kob-suggestion-author">${escapeHtml(s.createdByName)}</span>
                    <span class="kob-suggestion-date">${new Date(s.createdAt).toLocaleString('tr-TR')}</span>
                    <p class="kob-suggestion-text">${escapeHtml(s.text)}</p>
                  </div>
                `).join('')}
                ${canKobSuggest ? `<button data-kob-suggest-entry="${entry.id}" style="margin-top:6px">+ Yorum/öneri ekle</button>` : ''}
              </div>
            </div>
          `;
        }).join('')}
      </div>
      ${canEditSec ? `<button id="add-entry-btn" style="margin-bottom:12px">+ Yeni kayıt ekle</button>` : ''}
      ${entryEditorHtml}
      ${renderKobSuggestions(section)}
      <div class="actions" style="margin-top:12px">
        <button id="save-section-btn" ${canEditCurrentEntry ? '' : 'disabled'}>Kaydet</button>
        ${workflowButtons(section)}
      </div>
    `;
  }

  function renderKobSuggestions(section) {
    const suggestions = section.kobSuggestions || [];
    if (!suggestions.length) return '';
    return `
      <div class="card">
        <h3>KÖB önerileri</h3>
        ${suggestions.map((suggestion) => `
          <p><strong>${escapeHtml(suggestion.createdByName)}:</strong> ${escapeHtml(suggestion.text)}</p>
        `).join('')}
        <p class="muted">KÖB önerileri içeriği otomatik değiştirmez. DB veya KBY uygun görürse metne kendisi işler.</p>
      </div>
    `;
  }

  function workflowButtons(section) {
    const buttons = [];
    if (canPerformSectionAction(section, 'DBY_APPROVE')) {
      buttons.push('<button data-action="DBY_APPROVE">Daire Başkanı onayına sun</button>');
    }
    if (canPerformSectionAction(section, 'DB_APPROVE')) {
      buttons.push(`<button class="primary" data-action="DB_APPROVE">${section.directChairApproval ? 'Tüm Kayıtları Onayla → Kurul Başkanı\'na Gönder' : 'Tüm Kayıtları Onayla → Başkan Yardımcısı\'na Gönder'}</button>`);
    }
    if (canPerformSectionAction(section, 'DB_RETURN')) {
      buttons.push('<button data-action="DB_RETURN">Daireye iade et</button>');
    }
    if (canPerformSectionAction(section, 'DB_RETRACT')) {
      buttons.push('<button data-action="DB_RETRACT">Başkan Yardımcısı onayından geri çek</button>');
    }
    if (canPerformSectionAction(section, 'KBY_APPROVE')) {
      buttons.push('<button class="primary" data-action="KBY_APPROVE">Tüm Kayıtları Onayla → Kurul Başkanı\'na Gönder</button>');
    }
    if (canPerformSectionAction(section, 'KBY_RETURN')) {
      buttons.push('<button data-action="KBY_RETURN">Daireye iade et</button>');
    }
    if (canPerformSectionAction(section, 'KBY_RETRACT')) {
      buttons.push('<button data-action="KBY_RETRACT">Kurul Başkanı onayından geri çek</button>');
    }
    return buttons.join('');
  }

  function sectionDepartment(section) {
    if (!section || !section.departmentId) return null;
    return state.departments.find((department) => department.id === section.departmentId) || null;
  }

  function isSectionInUserScope(section, user = activeUser()) {
    if (!section || !user) return false;
    if (user.roleCode === 'ADMIN') return true;
    if (!section.departmentId) return false;
    if (user.roleCode === 'KBY') {
      const department = sectionDepartment(section);
      return section.responsibleKbyUserId === user.id || (department && department.reportsToUserId === user.id);
    }
    return user.departmentId === section.departmentId;
  }

  function canActAsSectionPreparer(section, user = activeUser()) {
    if (!isSectionInUserScope(section, user)) return false;
    return ['ADMIN', 'DBY', 'DB', 'KBY'].includes(user.roleCode);
  }

  function canActAsDby(section, user = activeUser()) {
    if (!isSectionInUserScope(section, user)) return false;
    return ['ADMIN', 'DBY', 'DB', 'KBY'].includes(user.roleCode);
  }

  function canActAsDb(section, user = activeUser()) {
    if (!isSectionInUserScope(section, user)) return false;
    return ['ADMIN', 'DB'].includes(user.roleCode);
  }

  function canActAsKby(section, user = activeUser()) {
    return user.roleCode === 'ADMIN' || (user.roleCode === 'KBY' && isSectionInUserScope(section, user));
  }

  function canPerformSectionAction(section, action, user = activeUser()) {
    if (!section || section.status === 'KILITLI') return false;
    if (action === 'MARK_NO_CONTENT') {
      if (!['SECTION_PREP', 'DBY_REVIEW', 'DB_APPROVAL'].includes(section.status)) return false;
      if (['ADMIN', 'KOB', 'KOB_PERSONELI'].includes(user.roleCode)) return true;
      if (canActAsKby(section, user)) return true;
      return canActAsDb(section, user);
    }
    if (action === 'REVERT_NO_CONTENT') {
      if (section.status !== 'NO_CONTENT') return false;
      if (['ADMIN', 'KOB', 'KOB_PERSONELI'].includes(user.roleCode)) return true;
      if (canActAsKby(section, user)) return true;
      return canActAsDb(section, user);
    }
    if (action === 'DBY_APPROVE') return section.status === 'SECTION_PREP' && isSectionInUserScope(section, user) && user.roleCode === 'DBY';
    if (action === 'DBY_RETRACT') return section.status === 'DB_APPROVAL' && isSectionInUserScope(section, user) && user.roleCode === 'DBY' && section.version === section.dbySubmittedVersion;
    if (action === 'DB_APPROVE') return ['SECTION_PREP', 'DBY_REVIEW', 'DB_APPROVAL'].includes(section.status) && canActAsDb(section, user);
    if (action === 'DB_RETURN') return section.status === 'DB_APPROVAL' && canActAsDb(section, user);
    if (action === 'DB_RETRACT') return section.status === 'KBY_APPROVAL' && canActAsDb(section, user) && section.version === section.dbSubmittedVersion;
    if (action === 'KBY_APPROVE') return ['SECTION_PREP', 'DB_APPROVAL', 'KBY_APPROVAL'].includes(section.status) && canActAsKby(section, user);
    if (action === 'KBY_RETURN') return section.status === 'KBY_APPROVAL' && canActAsKby(section, user);
    if (action === 'KBY_RETRACT') return ['KOB_READY', 'KBY_APPROVED'].includes(section.status) && canActAsKby(section, user) && section.version === section.kbySubmittedVersion;
    if (action === 'KOB_SUGGEST') return section.status !== 'NO_CONTENT' && ['ADMIN', 'KOB', 'KOB_PERSONELI'].includes(user.roleCode);
    return false;
  }

  function canViewSection(section, user = activeUser()) {
    if (!section || !user) return false;
    if (section.status === 'NO_CONTENT') return user.roleCode === 'ADMIN' || canActAsDb(section, user);
    if (['ADMIN', 'KB', 'KOB'].includes(user.roleCode)) return true;
    if (user.roleCode === 'KOB_PERSONELI') return true;
    return isSectionInUserScope(section, user);
  }

  function bindWorkspaceEvents(bulletin, selectedSection, selectedEntry) {
    document.querySelectorAll('[data-section-id]').forEach((button) => {
      button.addEventListener('click', () => {
        selectedSectionId = button.dataset.sectionId;
        selectedEntryId = null;
        previewAllSections = false;
        render();
      });
    });
    document.getElementById('save-section-btn')?.addEventListener('click', () => saveSection(selectedSection, selectedEntry));
    document.getElementById('section-heading-group')?.addEventListener('change', (event) => {
      const subgroupSelect = document.getElementById('section-heading-subgroup');
      if (subgroupSelect) subgroupSelect.innerHTML = headingSubGroupOptions(event.target.value, '');
    });
    document.getElementById('entry-heading-group')?.addEventListener('change', (event) => {
      const subgroupSelect = document.getElementById('entry-heading-subgroup');
      if (subgroupSelect) subgroupSelect.innerHTML = headingSubGroupOptions(event.target.value, '');
    });
    const tableEl = document.getElementById('section-table');
    if (tableEl) {
      if (pendingMergeTable) {
        updateMergeTablePreview(pendingMergeTable);
      } else {
        updateTablePreview(tableEl.value);
      }
      tableEl.addEventListener('input', () => {
        if (!tableEl.value.startsWith('[Birleşik tablo')) {
          pendingMergeTable = null;
          updateTablePreview(tableEl.value);
        }
      });
      tableEl.addEventListener('paste', (e) => {
        const html = e.clipboardData?.getData('text/html');
        if (html && html.includes('<table')) {
          e.preventDefault();
          const parsed = htmlToStructuredTable(html);
          if (parsed) {
            pendingMergeTable = parsed;
            const totalCols = Math.max(...parsed.rows.map((r) => r.reduce((s, c) => s + (c.colspan || 1), 0)));
            tableEl.value = `[Birleşik tablo: ${parsed.rows.length} satır × ${totalCols} sütun — önizlemeye bakın]`;
            const ctrl = document.getElementById('merge-header-ctrl');
            const hInput = document.getElementById('merge-header-rows');
            if (ctrl) ctrl.style.display = 'flex';
            if (hInput) hInput.value = parsed.headerRows;
            updateMergeTablePreview(parsed);
            return;
          }
        }
        pendingMergeTable = null;
        const ctrl = document.getElementById('merge-header-ctrl');
        if (ctrl) ctrl.style.display = 'none';
        setTimeout(() => updateTablePreview(tableEl.value), 0);
      });
      document.getElementById('merge-header-rows')?.addEventListener('input', (e) => {
        if (pendingMergeTable) {
          const newHeaderRows = Math.max(0, parseInt(e.target.value) || 0);
          const rawRows = pendingMergeTable._rawRows || pendingMergeTable.rows;
          const remerged = autoMergeHeaderCells(rawRows.map((r) => r.map((c) => ({ ...c }))), newHeaderRows);
          pendingMergeTable.rows = remerged;
          pendingMergeTable.headerRows = newHeaderRows;
          updateMergeTablePreview(pendingMergeTable);
        }
      });
    }
    document.querySelectorAll('[data-action]').forEach((button) => {
      button.addEventListener('click', () => transitionSection(selectedSection, button.dataset.action));
    });
    document.getElementById('preview-show-all-btn')?.addEventListener('click', () => { previewAllSections = true; render(); });
    document.getElementById('edit-bulletin-btn')?.addEventListener('click', () => editBulletin(bulletin.id));
    document.getElementById('submit-to-chair-btn')?.addEventListener('click', () => assembleBulletin(bulletin));
    document.getElementById('publish-btn')?.addEventListener('click', () => publishBulletin(bulletin));
    document.querySelectorAll('[data-select-entry]').forEach((button) => {
      button.addEventListener('click', () => {
        selectedEntryId = button.dataset.selectEntry;
        render();
      });
    });
    document.getElementById('add-entry-btn')?.addEventListener('click', () => {
      if (selectedSection) addEntry(selectedSection);
    });
    document.querySelectorAll('[data-delete-entry]').forEach((button) => {
      button.addEventListener('click', () => {
        if (selectedSection && confirm('Bu kaydı silmek istediğinizden emin misiniz?')) {
          deleteEntry(selectedSection, button.dataset.deleteEntry);
        }
      });
    });
    document.querySelectorAll('[data-approve-entry]').forEach((button) => {
      button.addEventListener('click', () => { if (selectedSection) approveEntry(selectedSection, button.dataset.approveEntry); });
    });
    document.querySelectorAll('[data-return-entry]').forEach((button) => {
      button.addEventListener('click', () => { if (selectedSection) returnEntry(selectedSection, button.dataset.returnEntry); });
    });
    document.querySelectorAll('[data-revoke-entry]').forEach((button) => {
      button.addEventListener('click', () => { if (selectedSection) revokeEntry(selectedSection, button.dataset.revokeEntry); });
    });
    document.querySelectorAll('[data-toggle-kob-suggestions]').forEach((button) => {
      button.addEventListener('click', () => {
        const panel = document.getElementById(`kob-suggestions-${button.dataset.toggleKobSuggestions}`);
        if (panel) panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      });
    });
    document.querySelectorAll('[data-kob-suggest-entry]').forEach((button) => {
      button.addEventListener('click', () => { if (selectedSection) addEntryKobSuggestion(selectedSection, button.dataset.kobSuggestEntry); });
    });
    document.querySelectorAll('[data-kob-no-content]').forEach((button) => {
      button.addEventListener('click', () => {
        const section = state.sections.find((s) => s.id === button.dataset.kobNoContent);
        if (section) transitionSection(section, 'MARK_NO_CONTENT');
      });
    });
    document.querySelectorAll('[data-kob-revert-no-content]').forEach((button) => {
      button.addEventListener('click', () => {
        const section = state.sections.find((s) => s.id === button.dataset.kobRevertNoContent);
        if (section) transitionSection(section, 'REVERT_NO_CONTENT');
      });
    });
    document.querySelectorAll('[data-card-no-content]').forEach((button) => {
      button.addEventListener('click', () => {
        const section = state.sections.find((s) => s.id === button.dataset.cardNoContent);
        if (section && confirm(`"${section.title}" bölümünü Veri Yok olarak işaretlemek istediğinizden emin misiniz?`)) transitionSection(section, 'MARK_NO_CONTENT');
      });
    });
    document.querySelectorAll('[data-card-revert-no-content]').forEach((button) => {
      button.addEventListener('click', () => {
        const section = state.sections.find((s) => s.id === button.dataset.cardRevertNoContent);
        if (section) transitionSection(section, 'REVERT_NO_CONTENT');
      });
    });
  }

  function canEditSection(section) {
    if (!section || section.status === 'KILITLI') return false;
    if (activeUser().roleCode === 'ADMIN') return true;
    if (section.status === 'SECTION_PREP') return canActAsSectionPreparer(section);
    if (section.status === 'DBY_REVIEW') return canActAsDby(section);
    if (section.status === 'DB_APPROVAL') return canActAsDb(section);
    if (section.status === 'KBY_APPROVAL') return canActAsKby(section);
    return false;
  }

  function canEditEntry(entry, section) {
    if (!canEditSection(section)) return false;
    if (activeUser().roleCode === 'ADMIN') return true;
    const user = activeUser();
    if (entry.createdBy === user.id) return true;
    if (canActAsDb(section, user)) return true;
    if (canActAsKby(section, user)) return true;
    const userRank = ROLE_RANK[user.roleCode] ?? 99;
    const creatorRank = ROLE_RANK[entry.createdByRole] ?? 99;
    return userRank <= creatorRank;
  }

  function canDeleteEntry(entry, section) {
    if (!section || section.status === 'KILITLI') return false;
    if (activeUser().roleCode === 'ADMIN') return true;
    const status = entry.approvalStatus || 'DRAFT';
    if (status === 'APPROVED') return false;
    const user = activeUser();
    const sectionOpen = !['PUBLISHED', 'ARCHIVED', 'KILITLI'].includes(section.status);
    if (entry.createdBy === user.id && sectionOpen) return true;
    if (!canEditSection(section)) return false;
    return canActAsDb(section, user) || canActAsKby(section, user);
  }

  function canApproveEntry(entry) {
    if (!entry || entry.approvalStatus !== 'PENDING') return false;
    const requiredRole = ROLE_SUPERIOR[entry.createdByRole];
    if (!requiredRole) return false;
    const user = activeUser();
    return user.roleCode === 'ADMIN' || user.roleCode === requiredRole;
  }

  function canRevokeEntry(entry) {
    if (!entry || entry.approvalStatus !== 'APPROVED') return false;
    const requiredRole = ROLE_SUPERIOR[entry.createdByRole];
    if (!requiredRole) return false;
    const user = activeUser();
    return user.roleCode === 'ADMIN' || user.roleCode === requiredRole;
  }

  function saveSection(section, entry) {
    if (!canEditSection(section)) return;
    const oldTitle = section.title;
    const newTitle = document.getElementById('section-title').value.trim();
    const newHeadingGroup = document.getElementById('section-heading-group')?.value || '';
    const newHeadingSubGroup = document.getElementById('section-heading-subgroup')?.value || '';

    let hasChanged = newTitle !== oldTitle
      || newHeadingGroup !== section.headingGroupCode
      || newHeadingSubGroup !== section.headingSubGroupCode;

    section.title = newTitle;
    section.headingGroupCode = newHeadingGroup;
    section.headingSubGroupCode = newHeadingSubGroup;
    section.preparedBy = section.preparedBy || activeUser().id;
    section.lastEditedBy = activeUser().id;

    let entryOldContent = null;
    let entryNewContent = null;

    if (entry) {
      const newEntryGroup = document.getElementById('entry-heading-group')?.value || '';
      const newEntrySub = document.getElementById('entry-heading-subgroup')?.value || '';
      if (newEntryGroup !== (entry.headingGroupCode || '') || newEntrySub !== (entry.headingSubGroupCode || '')) hasChanged = true;
      entry.headingGroupCode = newEntryGroup;
      entry.headingSubGroupCode = newEntrySub;

      const oldUserTable = (entry.structuredTables || []).find((t) => t._userEntered);
      const oldTableText = oldUserTable
        ? (oldUserTable._hasMerge ? '[birleşik]' : oldUserTable.rows.map((r) => r.join('\t')).join('\n'))
        : tableToText(entry.tables);
      const newContent = document.getElementById('section-content').value;
      const rawTable = document.getElementById('section-table').value;
      const userTable = pendingMergeTable || tsvToStructuredTable(rawTable);
      const nonUserTables = (entry.structuredTables || []).filter((t) => !t._userEntered);

      if (newContent !== entry.contentHtml || rawTable.trim() !== oldTableText.trim()) hasChanged = true;

      entryOldContent = [entry.contentHtml, oldTableText.trim()].filter(Boolean).join('\n---\n') || null;
      entryNewContent = [newContent, rawTable.trim()].filter(Boolean).join('\n---\n') || null;

      entry.contentHtml = newContent;
      entry.structuredTables = userTable ? [...nonUserTables, userTable] : nonUserTables;
      entry.tables = [];

      const userRole = activeUser().roleCode;
      entry.createdBy = entry.createdBy || activeUser().id;
      entry.createdByRole = entry.createdByRole || userRole;
      if (userRole === 'ADMIN' || userRole === 'KB' || !ROLE_SUPERIOR[userRole]) {
        entry.approvalStatus = 'APPROVED';
        entry.approvedBy = activeUser().id;
        entry.approvedAt = isoNow();
      } else {
        entry.approvalStatus = 'PENDING';
      }
      hasChanged = true;
    }

    if (hasChanged) {
      section.version += 1;
      addLog('SECTION_UPDATED', {
        bulletinId: section.bulletinId,
        sectionId: section.id,
        entryId: entry?.id || null,
        oldValueSummary: `${oldTitle} / v${section.version - 1}`,
        newValueSummary: `${section.title} / v${section.version}`,
        versionAfter: section.version,
        oldContent: entryOldContent,
        newContent: entryNewContent
      });
    }
    persist();
    render();
  }

  function makeEntry(order, section) {
    return { id: uid('entry'), order, contentHtml: '', structuredTables: [], tables: [],
      approvalStatus: 'DRAFT', createdBy: null, createdByRole: null, approvedBy: null, approvedAt: null,
      headingGroupCode: section?.headingGroupCode || '',
      headingSubGroupCode: section?.headingSubGroupCode || '' };
  }

  function addEntry(section) {
    const entries = section.entries || [];
    const maxOrder = entries.reduce((m, e) => Math.max(m, e.order || 0), 0);
    const newEntry = makeEntry(maxOrder + 1, section);
    section.entries = [...entries, newEntry];
    selectedEntryId = newEntry.id;
    persist();
    render();
  }

  function deleteEntry(section, entryId) {
    const entryToDelete = (section.entries || []).find((e) => e.id === entryId);
    if (!entryToDelete || !canDeleteEntry(entryToDelete, section)) return;
    const remaining = (section.entries || []).filter((e) => e.id !== entryId);
    remaining.forEach((e, i) => { e.order = i + 1; });
    section.entries = remaining;
    if (selectedEntryId === entryId) {
      selectedEntryId = remaining.length > 0 ? remaining[0].id : null;
    }
    section.version += 1;
    addLog('SECTION_UPDATED', {
      bulletinId: section.bulletinId,
      sectionId: section.id,
      oldValueSummary: 'Kayıt silindi',
      newValueSummary: `${remaining.length} kayıt`,
      versionAfter: section.version
    });
    persist();
    render();
  }

  function approveEntry(section, entryId) {
    const entry = (section.entries || []).find((e) => e.id === entryId);
    if (!entry || !canApproveEntry(entry)) return;
    entry.approvalStatus = 'APPROVED';
    entry.approvedBy = activeUser().id;
    entry.approvedAt = isoNow();
    addLog('ENTRY_APPROVED', {
      bulletinId: section.bulletinId, sectionId: section.id, entryId: entry.id,
      newValueSummary: `Kayıt ${entry.order} onaylandı`
    });
    persist();
    render();
  }

  function returnEntry(section, entryId) {
    const entry = (section.entries || []).find((e) => e.id === entryId);
    if (!entry || !canApproveEntry(entry)) return;
    const reason = prompt('İade gerekçesi', 'Düzeltme gerekiyor');
    if (!reason) return;
    entry.approvalStatus = 'RETURNED';
    entry.returnedBy = activeUser().id;
    entry.returnedAt = isoNow();
    entry.returnReason = reason;
    addLog('ENTRY_RETURNED', {
      bulletinId: section.bulletinId, sectionId: section.id, entryId: entry.id,
      newValueSummary: `Kayıt ${entry.order} iade edildi`, reason
    });
    persist();
    render();
  }

  function revokeEntry(section, entryId) {
    const entry = (section.entries || []).find((e) => e.id === entryId);
    if (!entry || !canRevokeEntry(entry)) return;
    entry.approvalStatus = 'RETURNED';
    entry.approvedBy = null;
    entry.approvedAt = null;
    addLog('ENTRY_REVOKED', {
      bulletinId: section.bulletinId, sectionId: section.id, entryId: entry.id,
      newValueSummary: `Kayıt ${entry.order} onayı kaldırıldı`
    });
    persist();
    render();
  }

  function addEntryKobSuggestion(section, entryId) {
    if (!['KOB', 'KOB_PERSONELI', 'ADMIN'].includes(activeUser().roleCode)) return;
    if (section.status === 'KILITLI') return;
    const entry = (section.entries || []).find((e) => e.id === entryId);
    if (!entry) return;
    const text = prompt('KÖB önerisi / yorumu:');
    if (!text || !text.trim()) return;
    entry.kobSuggestions = entry.kobSuggestions || [];
    entry.kobSuggestions.push({
      id: uid('kob-sug'),
      text: text.trim(),
      createdBy: activeUser().id,
      createdByName: activeUser().fullName,
      createdAt: isoNow()
    });
    addLog('KOB_SUGGESTION_CREATED', {
      bulletinId: section.bulletinId,
      sectionId: section.id,
      newValueSummary: `Kayıt ${entry.order} için KÖB önerisi eklendi`
    });
    persist();
    render();
  }

  function transitionSection(section, action) {
    if (!canPerformSectionAction(section, action)) {
      alert('Bu işlem için yetkiniz yok.');
      return;
    }
    const reason = action.includes('RETURN') ? prompt('İade gerekçesi', 'Düzeltme gerekiyor') : null;
    const before = section.status;
    if (action === 'MARK_NO_CONTENT') {
      section.entries = (section.entries || []).filter((e) => e.approvalStatus === 'APPROVED');
      section.entries.forEach((e, i) => { e.order = i + 1; });
      section.status = 'NO_CONTENT';
      addApproval(section, 'NO_CONTENT', 'APPROVED', 'Bu hafta veri yok');
    }
    if (action === 'REVERT_NO_CONTENT') section.status = 'SECTION_PREP';
    if (action === 'DBY_APPROVE') {
      section.status = 'DB_APPROVAL';
      section.dbySubmittedVersion = section.version;
      section.reviewedByDby = activeUser().id;
      section.reviewedByDbyAt = isoNow();
      addApproval(section, 'DBY_REVIEW', 'APPROVED', null);
    }
    if (action === 'DBY_RETRACT') {
      section.status = 'SECTION_PREP';
      section.dbySubmittedVersion = null;
      addApproval(section, 'DBY_REVIEW', 'RETURNED', 'DBY geri çekti');
    }
    if (action === 'DB_APPROVE') {
      section.dbApprovalFromStatus = section.status;
      section.approvedByDb = activeUser().id;
      section.approvedByDbAt = isoNow();
      section.dbSubmittedVersion = section.version;
      section.status = section.directChairApproval ? 'KOB_READY' : 'KBY_APPROVAL';
      addApproval(section, 'DB_APPROVAL', 'APPROVED', null);
      const now = isoNow();
      (section.entries || []).forEach((entry) => {
        entry.approvalStatus = 'APPROVED';
        entry.approvedBy = activeUser().id;
        entry.approvedAt = now;
      });
    }
    if (action === 'DB_RETURN') {
      section.status = 'SECTION_PREP';
      section.dbySubmittedVersion = null;
      section.dbApprovalFromStatus = null;
    }
    if (action === 'DB_RETRACT') {
      section.status = section.dbApprovalFromStatus || 'SECTION_PREP';
      section.dbSubmittedVersion = null;
      section.dbApprovalFromStatus = null;
      addApproval(section, 'DB_APPROVAL', 'RETURNED', 'DB geri çekti');
    }
    if (action === 'KBY_APPROVE') {
      section.kbyApprovalFromStatus = section.status;
      section.approvedByKby = activeUser().id;
      section.approvedByKbyAt = isoNow();
      section.kbySubmittedVersion = section.version;
      section.status = 'KBY_APPROVED';
      addApproval(section, 'KBY_APPROVAL', 'APPROVED', null);
      const now = isoNow();
      (section.entries || []).forEach((entry) => {
        entry.approvalStatus = 'APPROVED';
        entry.approvedBy = activeUser().id;
        entry.approvedAt = now;
      });
    }
    if (action === 'KBY_RETURN') {
      section.status = 'DB_APPROVAL';
      section.dbSubmittedVersion = null;
      section.kbyApprovalFromStatus = null;
    }
    if (action === 'KBY_RETRACT') {
      section.status = section.kbyApprovalFromStatus || 'KBY_APPROVAL';
      section.kbySubmittedVersion = null;
      section.kbyApprovalFromStatus = null;
      addApproval(section, 'KBY_APPROVAL', 'RETURNED', 'KBY geri çekti');
    }
    if (action === 'KOB_SUGGEST') {
      const suggestion = prompt('KÖB önerisi', 'Düzeltme önerisi');
      if (!suggestion) return;
      section.kobSuggestions = section.kobSuggestions || [];
      section.kobSuggestions.push({
        id: uid('suggestion'),
        text: suggestion,
        createdBy: activeUser().id,
        createdByName: activeUser().fullName,
        createdAt: isoNow(),
        status: 'OPEN'
      });
      addLog('KOB_SUGGESTION_CREATED', {
        bulletinId: section.bulletinId,
        sectionId: section.id,
        newValueSummary: suggestion,
        reason: 'KÖB doğrudan değişiklik yapmadan öneri oluşturdu'
      });
      persist();
      render();
      return;
    }
    if (action.includes('RETURN')) {
      section.rejectionReason = reason;
      addApproval(section, action.replace('_RETURN', ''), 'RETURNED', reason);
    }
    addLog(action, {
      bulletinId: section.bulletinId,
      sectionId: section.id,
      oldValueSummary: before,
      newValueSummary: section.status,
      reason
    });
    persist();
    render();
  }

  function addApproval(section, approvalType, decision, comment) {
    state.approvals.unshift({
      id: uid('approval'),
      bulletinId: section.bulletinId,
      sectionId: section.id,
      approvalType,
      approverUserId: activeUser().id,
      approverName: activeUser().fullName,
      approverRoleCode: activeUser().roleCode,
      decision,
      decisionAt: isoNow(),
      comment,
      sectionVersion: section.version
    });
  }

  function assembleBulletin(bulletin) {
    const sections = state.sections.filter((section) => section.bulletinId === bulletin.id);
    bulletin.status = 'CHAIR_APPROVAL';
    sections.forEach((section) => {
      if (section.status !== 'NO_CONTENT') section.status = 'KOB_READY';
    });
    addLog('BULLETIN_SUBMITTED_TO_CHAIR', { bulletinId: bulletin.id, newValueSummary: bulletin.title });
    persist();
    render();
  }

  function canChairApprove(bulletin) {
    const role = activeUser().roleCode;
    if (role !== 'KB' && role !== 'ADMIN') return false;
    if (bulletin.status === 'PUBLISHED') return false;
    if (bulletin.status === 'CHAIR_APPROVAL') return true;
    const sections = state.sections.filter((s) => s.bulletinId === bulletin.id);
    if (!sections.length) return false;
    return sections.every((s) => ['KBY_APPROVED', 'NO_CONTENT', 'KOB_READY'].includes(s.status));
  }

  function canSubmitToChair(bulletin) {
    const role = activeUser().roleCode;
    if (!['ADMIN', 'KBY'].includes(role)) return false;
    if (['PUBLISHED', 'CHAIR_APPROVAL'].includes(bulletin.status)) return false;
    const sections = state.sections.filter((s) => s.bulletinId === bulletin.id);
    if (!sections.length) return false;
    return sections.every((s) => ['KBY_APPROVED', 'NO_CONTENT', 'KOB_READY'].includes(s.status));
  }

  function canKobApprovePackage(bulletin) {
    const role = activeUser().roleCode;
    return (role === 'KOB' || role === 'ADMIN') && bulletin.status === 'KOB_REVIEW';
  }

  function kobApprovePackage(bulletin) {
    if (!canKobApprovePackage(bulletin)) return;
    bulletin.status = 'CHAIR_APPROVAL';
    state.sections.filter((section) => section.bulletinId === bulletin.id).forEach((section) => {
      section.status = 'KOB_READY';
    });
    state.approvals.unshift({
      id: uid('approval'),
      bulletinId: bulletin.id,
      sectionId: null,
      approvalType: 'KOB_PACKAGE_REVIEW',
      approverUserId: activeUser().id,
      approverName: activeUser().fullName,
      approverRoleCode: activeUser().roleCode,
      decision: 'APPROVED',
      decisionAt: isoNow(),
      comment: 'Paket kontrolü tamamlandı',
      sectionVersion: null
    });
    addLog('KOB_PACKAGE_APPROVED', { bulletinId: bulletin.id, newValueSummary: 'Başkan Onayı Bekliyor' });
    persist();
    render();
  }

  function publishBulletin(bulletin) {
    if (!canChairApprove(bulletin)) return;
    if (bulletin.status !== 'CHAIR_APPROVAL') {
      const sections = state.sections.filter((s) => s.bulletinId === bulletin.id);
      bulletin.status = 'CHAIR_APPROVAL';
      sections.forEach((s) => { if (s.status !== 'NO_CONTENT') s.status = 'KOB_READY'; });
      addLog('BULLETIN_SUBMITTED_TO_CHAIR', { bulletinId: bulletin.id, newValueSummary: bulletin.title });
    }
    const cleanHtml = bulletinPreview(bulletin.id, false, null, true);
    const loggedHtml = bulletinPreview(bulletin.id, true, null, true);
    const archive = {
      id: uid('archive'),
      bulletinId: bulletin.id,
      year: bulletin.year,
      weekNumber: bulletin.weekNumber,
      publishedPdfPath: 'browser-generated',
      loggedViewPath: 'localStorage-html-snapshot',
      snapshotJsonPath: bulletin.organizationSnapshotId,
      publishedAt: isoNow(),
      approvedByChair: activeUser().fullName,
      organizationSnapshot: state.organizationSnapshots?.find((item) => item.id === bulletin.organizationSnapshotId),
      cleanHtml,
      loggedHtml,
      cleanPdfHash: hashString(cleanHtml),
      loggedViewHash: hashString(loggedHtml),
      searchKeywords: makeSearchKeywords(bulletin.id)
    };
    state.archives.unshift(archive);
    bulletin.status = 'PUBLISHED';
    bulletin.publishedAt = archive.publishedAt;
    bulletin.approvedByChairAt = archive.publishedAt;
    bulletin.archiveRecordId = archive.id;
    state.sections.filter((section) => section.bulletinId === bulletin.id).forEach((section) => {
      section.status = 'KILITLI';
    });
    addApproval({ bulletinId: bulletin.id, id: null, version: null }, 'KB_FINAL_APPROVAL', 'APPROVED', null);
    addLog('BULLETIN_PUBLISHED', { bulletinId: bulletin.id, newValueSummary: archive.id });
    persist();
    currentView = 'archive';
    activateTab('archive');
    render();
  }

  function renderArchive() {
    app.innerHTML = `
      <section class="panel">
        <h2>Arşiv</h2>
        ${state.archives.length ? archiveList() : '<p class="muted">Yayımlanmış bülten yok.</p>'}
      </section>
    `;
  }

  function archiveList() {
    return state.archives.map((archive) => {
      const archiveId = archive.id;
      return `
      <div class="card">
        <div class="toolbar">
          <div>
            <h3>${archive.year}/${archive.weekNumber} Haftalık Bülten</h3>
            <p class="muted">Yayım: ${new Date(archive.publishedAt).toLocaleString('tr-TR')} - KB: ${escapeHtml(archive.approvedByChair)}</p>
            <p class="muted">Temiz özet: ${archive.cleanPdfHash} | Kayıtlı özet: ${archive.loggedViewHash}</p>
          </div>
          <div style="display:flex;gap:8px;">
            <button onclick="window.HaftalikBultenApp.printArchiveView('${archiveId}', 'clean')">Temiz PDF</button>
            <button onclick="window.HaftalikBultenApp.printArchiveView('${archiveId}', 'logged')">Kayıtlı PDF</button>
          </div>
        </div>
        <details>
          <summary>Temiz görünüm</summary>
          ${bulletinPreview(archive.bulletinId, false, null, true)}
        </details>
        <details>
          <summary>Kayıtlı görünüm</summary>
          ${bulletinPreview(archive.bulletinId, true, null, true)}
        </details>
      </div>
    `;
    }).join('');
  }

  function printArchiveView(archiveId, viewType) {
    const archive = state.archives.find((a) => a.id === archiveId);
    if (!archive) return;
    const html = bulletinPreview(archive.bulletinId, viewType === 'logged', null, true);
    const title = `${archive.year}-${String(archive.weekNumber).padStart(2, '0')} Haftalık Bülten ${viewType === 'clean' ? '(Temiz)' : '(Kayıtlı)'}`;
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>${title}</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; color: #1e293b; margin: 0; padding: 24px; }
  * { box-sizing: border-box; }
  .preview { background: #fff; padding: 0; }
  .preview h2 { font-size: 1.35em; }
  .preview section > p { text-align: justify; }
  .preview-header-box { border: 1.5px solid #1a3a6b; outline: 1.5px solid #1a3a6b; outline-offset: -7px; padding: 24px 40px 20px; text-align: center; margin-bottom: 0; }
  .preview-logo { display: block; height: 84px; margin: 0 auto 12px; width: auto; }
  .preview-main-title { color: #1a3a6b; font-size: 18px; font-style: italic; font-weight: bold; line-height: 1.5; margin: 0; }
  .preview-meta { color: #1a3a6b; display: flex; font-size: 14px; font-weight: bold; justify-content: space-between; padding: 10px 2px 6px; }
  .preview-divider { border: none; border-top: 3px solid #1a3a6b; margin: 0 0 24px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border-bottom: 1px solid #e2e8f0; padding: 10px; text-align: left; vertical-align: top; }
  th { background: #f1f5f9; color: #334155; font-size: 12px; }
  .table-wrap { overflow: auto; }
  .structured-tables { display: grid; gap: 14px; margin-top: 12px; }
  .structured-table { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
  .structured-table h3 { background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-size: 13px; margin: 0; padding: 9px 10px; }
  .log-item { border-left: 4px solid #e2e8f0; padding: 6px 10px; margin-bottom: 6px; }
  .muted { color: #64748b; font-size: 12px; }
  .section-log-block { margin-top: 14px; padding-top: 10px; border-top: 1px dashed #e2e8f0; }
  .log-entry-row { border-left: 3px solid #cbd5e1; margin-bottom: 8px; padding: 5px 10px; }
  .log-meta { color: #64748b; display: block; font-size: 12px; }
  .log-reason { color: #b45309; font-style: italic; }
  .log-content-change { background: #f8fafc; border-left: 2px solid #3b82f6; font-size: 12px; margin-top: 5px; padding: 4px 8px; }
  .log-content-label { color: #475569; display: block; font-size: 11px; font-weight: 600; margin-bottom: 2px; text-transform: uppercase; }
  .log-content-text { color: #1e293b; white-space: pre-wrap; }
.preview-footer { border-top: 2px solid #1a3a6b; color: #1a3a6b; font-size: 11px; line-height: 1.6; margin-top: 32px; padding-top: 6px; }
  .preview-footer-row { padding: 2px 0; }
  .preview-footer strong { font-weight: 700; margin-right: 6px; }
  @media print {
    body { padding: 0; margin: 0; width: 210mm; padding-bottom: 48px; }
    @page { size: A4 portrait; margin: 1.5cm; }
    .table-wrap { overflow: visible; }
    table { page-break-inside: auto; }
    tr { page-break-inside: avoid; page-break-after: auto; }
    thead { display: table-header-group; }
    .preview-header-box { page-break-after: avoid; }
    section { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .preview-footer {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #fff;
      border-top: 2px solid #1a3a6b;
      padding: 6px 1.5cm 4px;
      margin-top: 0;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
  }
</style>
</head>
<body>${html}</body>
</html>`);
    win.document.close();
    win.focus();
    win.print();
  }

  const LOG_META = {
    BULLETIN_CREATED:              { label: 'Bülten oluşturuldu',                    cat: 'system'   },
    BULLETIN_UPDATED:              { label: 'Bülten bilgileri güncellendi',           cat: 'system'   },
    BULLETIN_DELETED:              { label: 'Bülten silindi',                         cat: 'system'   },
    BULLETIN_SUBMITTED_TO_CHAIR:   { label: 'Başkan onayına gönderildi',              cat: 'approval' },
    BULLETIN_PUBLISHED:            { label: 'Bülten yayımlandı',                      cat: 'approval' },
    ORGANIZATION_SNAPSHOT_CAPTURED:{ label: 'Organizasyon anlık kaydı alındı',        cat: 'system'   },
    OFFICIAL_DEPARTMENT_CHAIRS_SYNCED:{ label: 'Daire başkanı adları senkronize edildi', cat: 'org'   },
    ORG_DEPARTMENT_MOVED:          { label: 'Daire bağlantısı değiştirildi',          cat: 'org'      },
    USER_CREATED:                  { label: 'Kullanıcı oluşturuldu',                  cat: 'org'      },
    USER_UPDATED:                  { label: 'Kullanıcı güncellendi',                  cat: 'org'      },
    PERSONNEL_BULK_IMPORTED:       { label: 'Personel toplu aktarıldı',               cat: 'org'      },
    SECTION_UPDATED:               { label: 'Bölüm içeriği güncellendi',              cat: 'content'  },
    ENTRY_APPROVED:                { label: 'Kayıt onaylandı',                        cat: 'approval' },
    ENTRY_RETURNED:                { label: 'Kayıt iade edildi',                      cat: 'return'   },
    ENTRY_REVOKED:                 { label: 'Kayıt onayı geri alındı',               cat: 'return'   },
    KOB_SUGGESTION_CREATED:        { label: 'KÖB yorum / önerisi eklendi',            cat: 'content'  },
    KOB_PACKAGE_APPROVED:          { label: 'KÖB paketi onaylandı',                   cat: 'approval' },
    DBY_APPROVE:                   { label: 'Daire Başkan Yrd. onayı verildi',        cat: 'approval' },
    DBY_RETRACT:                   { label: 'Daire Başkan Yrd. onayı geri çekildi',   cat: 'return'   },
    DB_APPROVE:                    { label: 'Daire Başkanı onayı verildi',            cat: 'approval' },
    DB_RETURN:                     { label: 'Daire Başkanı daireye iade etti',        cat: 'return'   },
    DB_RETRACT:                    { label: 'Daire Başkanı onayı geri çekti',         cat: 'return'   },
    KBY_APPROVE:                   { label: 'Başkan Yardımcısı onayı verildi',        cat: 'approval' },
    KBY_RETURN:                    { label: 'Başkan Yardımcısı daireye iade etti',    cat: 'return'   },
    KBY_RETRACT:                   { label: 'Başkan Yardımcısı onayı geri çekti',     cat: 'return'   },
    MARK_NO_CONTENT:               { label: '"Bu hafta veri yok" işaretlendi',        cat: 'content'  },
    REVERT_NO_CONTENT:             { label: '"Veri yok" işareti kaldırıldı',          cat: 'content'  },
  };

  const LOG_CAT_LABELS = {
    system: 'Sistem', org: 'Organizasyon', content: 'İçerik', approval: 'Onay', return: 'İade / Geri Çekme'
  };
  const LOG_CAT_COLOR = {
    system: '#64748b', org: '#7c3aed', content: '#2563eb', approval: '#16a34a', return: '#ea580c'
  };

  function toTitleCase(s) {
    return String(s).replace(/\S+/g, (w) => w.charAt(0).toLocaleUpperCase('tr-TR') + w.slice(1).toLocaleLowerCase('tr-TR'));
  }

  function stripHtml(s) {
    return (s || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function contentDiffHtml(oldRaw, newRaw) {
    if (!oldRaw && !newRaw) return '';
    const parts = (oldRaw || '').split('\n---\n');
    const nparts = (newRaw || '').split('\n---\n');
    const oldText = stripHtml(parts[0] || '');
    const newText = stripHtml(nparts[0] || '');
    const oldTable = (parts[1] || '').trim();
    const newTable = (nparts[1] || '').trim();

    function lineDiff(a, b) {
      const aLines = a.split(/\n+/).map((l) => l.trim()).filter(Boolean);
      const bLines = b.split(/\n+/).map((l) => l.trim()).filter(Boolean);
      if (!aLines.length && !bLines.length) return '';
      if (a === b) return `<div style="color:#64748b;font-size:12px;padding:2px 0">Değişiklik yok</div>`;
      const aSet = new Set(aLines);
      const bSet = new Set(bLines);
      const removed = aLines.filter((l) => !bSet.has(l));
      const added   = bLines.filter((l) => !aSet.has(l));
      if (!removed.length && !added.length) return `<div style="color:#64748b;font-size:12px;padding:2px 0">Değişiklik yok (satır sırası değişti)</div>`;
      return [
        ...removed.map((l) => `<div style="background:#fef2f2;color:#b91c1c;padding:2px 6px;border-left:3px solid #f87171;font-size:12px;margin:1px 0">− ${escapeHtml(l)}</div>`),
        ...added.map((l)   => `<div style="background:#f0fdf4;color:#15803d;padding:2px 6px;border-left:3px solid #4ade80;font-size:12px;margin:1px 0">+ ${escapeHtml(l)}</div>`)
      ].join('');
    }

    const textDiff  = (oldText || newText)   ? `<div style="margin-bottom:4px"><span style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase">İçerik</span>${lineDiff(oldText, newText)}</div>` : '';
    const tableDiff = (oldTable || newTable) ? `<div><span style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase">Tablo</span>${lineDiff(oldTable, newTable)}</div>` : '';
    return textDiff + tableDiff;
  }

  function renderLogs() {
    const bulletins = state.bulletins;
    const activeBulletinId = logFilterBulletin === 'all' ? null : logFilterBulletin;

    let logs = state.logs;
    if (activeBulletinId) logs = logs.filter((l) => l.bulletinId === activeBulletinId);
    if (logFilterCategory !== 'all') logs = logs.filter((l) => (LOG_META[l.actionType]?.cat || 'system') === logFilterCategory);

    const bulletinName = (id) => {
      if (!id) return null;
      const b = bulletins.find((x) => x.id === id);
      return b ? escapeHtml(b.title) : null;
    };
    const sectionName = (id) => {
      if (!id) return null;
      const s = state.sections.find((x) => x.id === id);
      return s ? escapeHtml(s.title) : null;
    };

    app.innerHTML = `
      <section class="panel">
        <div class="toolbar" style="flex-wrap:wrap;gap:8px">
          <h2 style="margin:0">İşlem Kayıtları</h2>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <label style="margin:0">Bülten:</label>
            <select id="log-filter-bulletin">
              <option value="all">Tümü</option>
              ${bulletins.map((b) => `<option value="${b.id}"${logFilterBulletin === b.id ? ' selected' : ''}>${escapeHtml(b.title)}</option>`).join('')}
            </select>
            <label style="margin:0">Kategori:</label>
            <select id="log-filter-cat">
              <option value="all">Tümü</option>
              ${Object.entries(LOG_CAT_LABELS).map(([k, v]) => `<option value="${k}"${logFilterCategory === k ? ' selected' : ''}>${v}</option>`).join('')}
            </select>
            <span class="muted">${logs.length} kayıt</span>
          </div>
        </div>
      </section>
      <section class="panel">
        <div class="log-list">
          ${logs.length ? logs.map((log) => {
            const meta   = LOG_META[log.actionType] || { label: log.actionType, cat: 'system' };
            const color  = LOG_CAT_COLOR[meta.cat] || '#64748b';
            const bname  = bulletinName(log.bulletinId);
            const sname  = sectionName(log.sectionId);
            const diff   = log.actionType === 'SECTION_UPDATED' ? contentDiffHtml(log.oldContent, log.newContent) : '';
            const hasDiff = diff && diff.trim();
            return `
              <div class="log-item" style="border-left-color:${color};margin-bottom:10px">
                <div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap">
                  <strong style="color:${color}">${escapeHtml(meta.label)}</strong>
                  <span class="muted" style="font-size:12px">${new Date(log.createdAt).toLocaleString('tr-TR')}</span>
                </div>
                <div style="font-size:13px;margin:3px 0">
                  <strong>${escapeHtml(log.actorName)}</strong>
                  <span class="muted"> · ${escapeHtml(ROLE_LABELS[log.actorRole] || log.actorRole)}</span>
                  ${bname ? `<span class="muted"> · ${bname}</span>` : ''}
                  ${sname ? `<span class="muted"> · ${sname}</span>` : ''}
                </div>
                ${log.newValueSummary && !hasDiff ? `<div style="font-size:13px;color:#334155">${escapeHtml(log.newValueSummary)}</div>` : ''}
                ${log.reason ? `<div style="font-size:12px;color:#b45309;font-style:italic">Gerekçe: ${escapeHtml(log.reason)}</div>` : ''}
                ${hasDiff ? `<details style="margin-top:6px"><summary style="font-size:12px;cursor:pointer;color:#475569">İçerik değişikliğini göster</summary><div style="margin-top:6px">${diff}</div></details>` : ''}
              </div>`;
          }).join('') : '<p class="muted">Filtreyle eşleşen kayıt yok.</p>'}
        </div>
      </section>
    `;

    document.getElementById('log-filter-bulletin')?.addEventListener('change', (e) => {
      logFilterBulletin = e.target.value;
      render();
    });
    document.getElementById('log-filter-cat')?.addEventListener('change', (e) => {
      logFilterCategory = e.target.value;
      render();
    });
  }

  function formatBulletinDate(bulletin) {
    if (bulletin.bulletinDate) {
      const [y, m, d] = bulletin.bulletinDate.split('-');
      return `${d}.${m}.${y}`;
    }
    const src = bulletin.publishedAt || bulletin.createdAt;
    if (!src) return '';
    const dt = new Date(src);
    return isNaN(dt.getTime()) ? '' : dt.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function toRoman(n) {
    const v = [1000,900,500,400,100,90,50,40,10,9,5,4,1];
    const s = ['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I'];
    let r = '';
    for (let i = 0; i < v.length; i++) while (n >= v[i]) { r += s[i]; n -= v[i]; }
    return r;
  }

  function toAlpha(n) {
    let r = '';
    while (n > 0) { n--; r = String.fromCharCode(97 + (n % 26)) + r; n = Math.floor(n / 26); }
    return r;
  }

  function computePreviewLabels(bulletinId, providedSections = null) {
    const allSections = providedSections || state.sections.filter((s) => s.bulletinId === bulletinId);
    const entryItems = [];
    allSections.forEach((section) => {
      const rawEntries = (section.entries && section.entries.length > 0)
        ? section.entries
        : [{ id: null, order: 1, contentHtml: section.contentHtml || '', structuredTables: section.structuredTables || [], tables: section.tables || [] }];
      rawEntries.forEach((entry) => {
        entryItems.push({
          entry,
          section,
          groupCode: entry.headingGroupCode || section.headingGroupCode || '',
          subCode: entry.headingSubGroupCode || section.headingSubGroupCode || ''
        });
      });
    });

    const gi = (code) => state.headingGroups.findIndex((g) => g.code === code);
    entryItems.sort((a, b) => {
      const ga = gi(a.groupCode), gb = gi(b.groupCode);
      if (ga !== gb) return (ga < 0 ? 9999 : ga) - (gb < 0 ? 9999 : gb);
      const grp = state.headingGroups.find((g) => g.code === a.groupCode);
      const si = (code) => grp ? grp.children.findIndex(([c]) => c === code) : -1;
      const sa = si(a.subCode), sb = si(b.subCode);
      if (sa !== sb) return (sa < 0 ? 9999 : sa) - (sb < 0 ? 9999 : sb);
      return (a.entry.order || 0) - (b.entry.order || 0);
    });

    const groups = [];
    entryItems.forEach((item) => {
      const last = groups[groups.length - 1];
      if (last && last.groupCode === item.groupCode && last.subCode === item.subCode) {
        last.items.push(item);
      } else {
        groups.push({ groupCode: item.groupCode, subCode: item.subCode, items: [item] });
      }
    });

    const labelMap = new Map();
    let lastGroupCode = null;
    let groupNum = 0;
    let subNum = 0;

    const entryHasContent = (e) => (e.contentHtml || '').trim() || (e.structuredTables || []).length || (e.tables || []).length;
    const entryHasText = (e) => !!(e.contentHtml || '').trim();

    groups.forEach(({ groupCode, subCode, items: grpItems }) => {
      const grp = state.headingGroups.find((g) => g.code === groupCode);
      const sub = grp ? grp.children.find(([c]) => c === subCode) : null;
      const showH2 = groupCode && groupCode !== lastGroupCode;
      if (showH2) { groupNum++; subNum = 0; lastGroupCode = groupCode; }
      if (sub) subNum++;

      const filledCount = grpItems.filter((item) => entryHasText(item.entry)).length;
      const showNumbers = filledCount >= 1;
      let num = 0;

      grpItems.forEach(({ entry }) => {
        const hasText = entryHasText(entry);
        if (hasText) num++;
        const romanPart = grp ? toRoman(groupNum) : '';
        const alphaPart = sub ? ` ${toAlpha(subNum)})` : '';
        const numPart = (showNumbers && hasText) ? ` ${num}.` : '';
        const label = `${romanPart}${alphaPart}${numPart}`.trim();
        if (entry.id && label) labelMap.set(entry.id, label);
      });
    });

    return labelMap;
  }

  function bulletinPreview(bulletinId, includeLogs, contentSections = null, showFooter = false) {
    const bulletin = state.bulletins.find((item) => item.id === bulletinId);
    // Yapı ve numaralama her zaman bültendeki TÜM bölümlere göre yapılır.
    // contentSections verilmişse içerik (kayıt metni/tablolar) yalnızca o bölümler için gösterilir;
    // diğer bölümlerin başlıkları (H2/H3) görünür ama kayıtları gösterilmez.
    const allSections = state.sections.filter((section) => section.bulletinId === bulletinId);
    const contentSectionIds = contentSections ? new Set(contentSections.map((s) => s.id)) : null;
    const bulletinNo = `${bulletin.year}/${String(bulletin.weekNumber).padStart(2, '0')}`;
    const bulletinDateStr = formatBulletinDate(bulletin);

    const entryItems = [];
    allSections.forEach((section) => {
      const showContent = !contentSectionIds || contentSectionIds.has(section.id);
      const rawEntries = (section.entries && section.entries.length > 0)
        ? section.entries
        : [{ id: null, order: 1, contentHtml: section.contentHtml || '', structuredTables: section.structuredTables || [], tables: section.tables || [] }];
      rawEntries.forEach((entry) => {
        entryItems.push({
          entry,
          section,
          groupCode: entry.headingGroupCode || section.headingGroupCode || '',
          subCode: entry.headingSubGroupCode || section.headingSubGroupCode || '',
          showContent
        });
      });
    });

    const gi = (code) => state.headingGroups.findIndex((g) => g.code === code);
    entryItems.sort((a, b) => {
      const ga = gi(a.groupCode), gb = gi(b.groupCode);
      if (ga !== gb) return (ga < 0 ? 9999 : ga) - (gb < 0 ? 9999 : gb);
      const grp = state.headingGroups.find((g) => g.code === a.groupCode);
      const si = (code) => grp ? grp.children.findIndex(([c]) => c === code) : -1;
      const sa = si(a.subCode), sb = si(b.subCode);
      if (sa !== sb) return (sa < 0 ? 9999 : sa) - (sb < 0 ? 9999 : sb);
      return (a.entry.order || 0) - (b.entry.order || 0);
    });

    const groups = [];
    entryItems.forEach((item) => {
      const last = groups[groups.length - 1];
      if (last && last.groupCode === item.groupCode && last.subCode === item.subCode) {
        last.items.push(item);
      } else {
        groups.push({ groupCode: item.groupCode, subCode: item.subCode, items: [item] });
      }
    });

    let lastGroupCode = null;
    let groupNum = 0;
    let subNum = 0;
    const bodyHtml = groups.map(({ groupCode, subCode, items: grpItems }) => {
      const grp = state.headingGroups.find((g) => g.code === groupCode);
      const sub = grp ? grp.children.find(([c]) => c === subCode) : null;

      // Sayaçlar her zaman güncellenir — tüm bültendeki sıralamayı korur
      const showH2 = groupCode && groupCode !== lastGroupCode;
      if (showH2) { groupNum++; subNum = 0; lastGroupCode = groupCode; }
      if (sub) subNum++;
      const groupHeading = grp ? `${toRoman(groupNum)}- ${grp.title}` : '';
      const subHeading = sub ? `${toAlpha(subNum)}) ${sub[1]}` : '';

      const entryHasText = (e) => !!(e.contentHtml || '').trim();
      const filledCount = grpItems.filter(({ entry, showContent }) => showContent && entryHasText(entry)).length;
      const showNumbers = filledCount >= 1;
      let num = 0;
      const contentHtml = grpItems.map(({ entry, showContent }) => {
        if (!showContent) return '';
        const text = escapeHtml(entry.contentHtml || '').replace(/\n/g, '<br>');
        const hasTables = (entry.structuredTables || []).length || (entry.tables || []).length;
        if (!text && !hasTables) return '';
        const hasText = entryHasText(entry);
        if (hasText) num++;
        const prefix = (showNumbers && hasText) ? `<strong>${num}.</strong> ` : '';
        return `
          ${text ? `<p>${prefix}${text}</p>` : ''}
          ${(entry.structuredTables || []).filter((t) => !t._userEntered).length ? renderStructuredTables((entry.structuredTables || []).filter((t) => !t._userEntered)) : ''}
          ${(entry.structuredTables || []).filter((t) => t._userEntered).map((t) => `<div class="table-wrap">${renderTableFromRows(t.rows, t.headerRows)}</div>`).join('')}
          ${(entry.tables || []).length ? renderSectionTable(entry.tables) : ''}
          ${includeLogs ? renderEntryLogs(entry.id) : ''}
        `;
      }).join('');

      // Görünür içerik yoksa blok renderlanmaz (sayaçlar zaten güncellendi)
      if (!contentHtml.trim()) return '';
      return `
        <section>
          ${showH2 && groupHeading ? `<h2>${escapeHtml(groupHeading)}</h2>` : ''}
          ${subHeading ? `<h3>${escapeHtml(subHeading)}</h3>` : ''}
          ${contentHtml}
        </section>
      `;
    }).join('');

    return `
      <article class="preview">
        <div class="preview-header-box">
          <img src="images/spk-logo.png" class="preview-logo" alt="SPK" onerror="this.style.display='none'">
          <p class="preview-main-title">SERMAYE PİYASASI KURULU<br>BÜLTENİ</p>
        </div>
        <div class="preview-meta">
          <span>${escapeHtml(bulletinNo)}</span>
          <span>${escapeHtml(bulletinDateStr)}</span>
        </div>
        <hr class="preview-divider">
        ${bodyHtml}
        ${showFooter ? `
        <footer class="preview-footer">
          <div class="preview-footer-row">
            <strong>MERKEZ</strong>
            Eskişehir Yolu 8.Km No:156 06530 ANKARA &nbsp;|&nbsp; Tel: (312) 292 90 90 &nbsp;|&nbsp; Faks: (312) 292 90 00 &nbsp;|&nbsp; www.spk.gov.tr
          </div>
          <div class="preview-footer-row">
            <strong>İSTANBUL TEMSİLCİLİĞİ</strong>
            Harbiye Mah. Askerocağı Cad. No:15 34367 Şişli İSTANBUL &nbsp;|&nbsp; Tel: (212) 334 55 00 &nbsp;|&nbsp; Faks: (212) 334 56 00
          </div>
        </footer>` : ''}
      </article>
    `;
  }

  function isNumericCell(text) {
    return /^[+\-]?[\d.,\s]+%?$/.test((text || '').trim()) && (text || '').trim().length > 0;
  }

  function renderSectionTable(rows) {
    return `
      <table>
        <thead><tr><th>Başlık</th><th style="text-align:center">Değer</th><th>Açıklama</th></tr></thead>
        <tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.name)}</td><td style="text-align:center">${escapeHtml(row.value)}</td><td>${escapeHtml(row.note)}</td></tr>`).join('')}</tbody>
      </table>
    `;
  }

  function renderStructuredTables(tables) {
    return `
      <div class="structured-tables">
        ${tables.map((table) => `
            <div class="structured-table">
              <h3>${escapeHtml(table.title || 'Tablo')}${table.page ? ` <span class="muted">Sayfa ${escapeHtml(table.page)}</span>` : ''}</h3>
              <div class="table-wrap">${renderTableFromRows(table.rows || [], table.headerRows)}</div>
            </div>
          `).join('')}
      </div>
    `;
  }

  const ACTION_TYPE_LABELS = {
    SECTION_UPDATED: 'İçerik güncellendi',
    ENTRY_APPROVED: 'Kayıt onaylandı',
    ENTRY_RETURNED: 'Kayıt iade edildi',
    ENTRY_REVOKED: 'Onay kaldırıldı',
    SECTION_SUBMITTED: 'Bölüm gönderildi',
    DBY_REVIEW: 'Daire Başkan Yrd. incelemesine alındı',
    DB_APPROVAL: 'Daire Başkanı onayına gönderildi',
    KBY_APPROVAL: 'Başkan Yardımcısı onayına gönderildi',
    KBY_APPROVED: 'Başkan Yardımcısı onayladı',
    KB_APPROVAL: 'Kurul Başkanı onayına gönderildi',
    NO_CONTENT: 'Veri yok olarak işaretlendi'
  };

  function renderEntryLogs(entryId) {
    const logs = state.logs.filter((log) => log.entryId === entryId);
    if (!logs.length) return '';
    return `
      <div class="section-log-block">
        <h4 style="margin:16px 0 6px;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.05em;">İşlem Geçmişi</h4>
        ${logs.map((log) => {
          const label = ACTION_TYPE_LABELS[log.actionType] || log.actionType;
          const roleLabel = ROLE_LABELS[log.actorRole] || log.actorRole;
          const dateStr = new Date(log.createdAt).toLocaleString('tr-TR');
          let contentBlock = '';
          if (log.newContent) {
            const oldLines = log.oldContent ? log.oldContent.split('\n---\n') : [];
            const newLines = log.newContent.split('\n---\n');
            const newText = newLines[0] || '';
            const oldText = oldLines[0] || '';
            if (newText && newText !== oldText) {
              contentBlock += `<div class="log-content-change"><span class="log-content-label">Yeni içerik:</span><span class="log-content-text">${escapeHtml(newText)}</span></div>`;
            }
            if (newLines[1]) {
              contentBlock += `<div class="log-content-change"><span class="log-content-label">Tablo verisi:</span><span class="log-content-text">${escapeHtml(newLines[1])}</span></div>`;
            }
          }
          const reasonBlock = log.reason ? `<span class="log-reason"> — Gerekçe: ${escapeHtml(log.reason)}</span>` : '';
          return `
            <div class="log-entry-row">
              <span class="log-meta">${dateStr} · <strong>${escapeHtml(log.actorName)}</strong> (${escapeHtml(roleLabel)}) · ${escapeHtml(label)}${reasonBlock}</span>
              ${contentBlock}
            </div>`;
        }).join('')}
      </div>
    `;
  }

  function renderSectionLogs(sectionId) {
    const logs = state.logs.filter((log) => log.sectionId === sectionId);
    if (!logs.length) return '<p class="muted">Bu bölüm için işlem kaydı yok.</p>';
    return `
      <div class="section-log-block">
        <h4 style="margin:16px 0 6px;color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:.05em;">İşlem Geçmişi</h4>
        ${logs.map((log) => {
          const label = ACTION_TYPE_LABELS[log.actionType] || log.actionType;
          const roleLabel = ROLE_LABELS[log.actorRole] || log.actorRole;
          const dateStr = new Date(log.createdAt).toLocaleString('tr-TR');
          let contentBlock = '';
          if (log.newContent) {
            const oldLines = log.oldContent ? log.oldContent.split('\n---\n') : [];
            const newLines = log.newContent.split('\n---\n');
            const newText = newLines[0] || '';
            const oldText = oldLines[0] || '';
            if (newText && newText !== oldText) {
              contentBlock += `<div class="log-content-change"><span class="log-content-label">Yeni içerik:</span><span class="log-content-text">${escapeHtml(newText)}</span></div>`;
            }
            if (newLines[1]) {
              contentBlock += `<div class="log-content-change"><span class="log-content-label">Tablo verisi:</span><span class="log-content-text">${escapeHtml(newLines[1])}</span></div>`;
            }
          }
          const reasonBlock = log.reason ? `<span class="log-reason"> — Gerekçe: ${escapeHtml(log.reason)}</span>` : '';
          return `
            <div class="log-entry-row">
              <span class="log-meta">${dateStr} · <strong>${escapeHtml(log.actorName)}</strong> (${escapeHtml(roleLabel)}) · ${escapeHtml(label)}${reasonBlock}</span>
              ${contentBlock}
            </div>`;
        }).join('')}
      </div>
    `;
  }

  function renderSectionTableText(rows) {
    return rows.map((row) => `${row.name} | ${row.value} | ${row.note}`).join('\n');
  }

  function tableToText(rows) {
    return renderSectionTableText(rows || []);
  }

  function textToTable(text) {
    return text.split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split('|').map((part) => part.trim());
        return { name: parts[0] || '', value: parts[1] || '', note: parts[2] || '' };
      });
  }

  function htmlToStructuredTable(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    const table = div.querySelector('table');
    if (!table) return null;
    const rows = [];
    let headerRows = 0;
    Array.from(table.querySelectorAll('tr')).forEach((tr) => {
      const inThead = !!tr.closest('thead');
      const thCount = tr.querySelectorAll('th').length;
      const tdCount = tr.querySelectorAll('td').length;
      const isHeader = inThead || (thCount > 0 && tdCount === 0);
      const cells = [];
      tr.querySelectorAll('th, td').forEach((cell) => {
        cells.push({
          text: cell.textContent.replace(/\s+/g, ' ').trim(),
          colspan: parseInt(cell.getAttribute('colspan') || '1', 10),
          rowspan: parseInt(cell.getAttribute('rowspan') || '1', 10),
        });
      });
      if (cells.length) { rows.push(cells); if (isHeader) headerRows++; }
    });
    if (!rows.length) return null;
    const detectedHeaderRows = headerRows || 1;
    const mergedRows = autoMergeHeaderCells(rows, detectedHeaderRows);
    const hasMerge = mergedRows.some((row) => row.some((c) => c.colspan > 1 || c.rowspan > 1));
    if (!hasMerge) {
      return { _userEntered: true, title: 'Tablo', rows: mergedRows.map((r) => r.map((c) => c.text)) };
    }
    return { _userEntered: true, _hasMerge: true, headerRows: detectedHeaderRows, title: 'Tablo', rows: mergedRows, _rawRows: rows };
  }

  function autoMergeHeaderCells(rows, headerRows) {
    if (!rows || rows.length < 1) return rows;
    const result = rows.map((r) => r.map((c) => ({ ...c })));

    // Adım 1: Başlık satırlarında sağdaki boş hücreleri önceki hücrenin colspan'ına ekle
    for (let ri = 0; ri < Math.min(headerRows, result.length); ri++) {
      const row = result[ri];
      const merged = [];
      for (let i = 0; i < row.length; i++) {
        if (!row[i].text.trim() && merged.length > 0) {
          merged[merged.length - 1].colspan = (merged[merged.length - 1].colspan || 1) + 1;
        } else {
          merged.push(row[i]);
        }
      }
      result[ri] = merged;
    }

    // Adım 2: headerRows >= 2 ise, 1. satırdaki hücrenin kapladığı sütunlarda
    // 2. satır tamamen boşsa rowspan=2 uygula ve 2. satırdan o hücreleri kaldır
    if (headerRows >= 2 && result.length >= 2) {
      const row0 = result[0];
      const row1 = result[1];

      let col = 0;
      const row0Starts = row0.map((c) => { const s = col; col += (c.colspan || 1); return s; });

      col = 0;
      const row1Starts = row1.map((c) => { const s = col; col += (c.colspan || 1); return s; });

      const removeFromRow1 = new Set();
      row0.forEach((cell, i) => {
        if ((cell.rowspan || 1) > 1) return;
        const start = row0Starts[i];
        const end = start + (cell.colspan || 1);
        const covered = row1.reduce((acc, r1c, j) => {
          const r1s = row1Starts[j];
          const r1e = r1s + (r1c.colspan || 1);
          if (r1s >= start && r1e <= end) acc.push(j);
          return acc;
        }, []);
        if (covered.length > 0 && covered.every((j) => !(row1[j].text || '').trim())) {
          cell.rowspan = 2;
          covered.forEach((j) => removeFromRow1.add(j));
        }
      });

      result[1] = row1.filter((_, i) => !removeFromRow1.has(i));
    }

    return result;
  }

  function tsvToStructuredTable(text) {
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return null;
    const hasTabs = lines.some((l) => l.includes('\t'));
    let rows;
    if (hasTabs) {
      rows = lines.map((line) => line.split('\t').map((c) => c.trim()));
    } else if (lines.some((l) => l.includes('|'))) {
      rows = lines.map((line) => {
        const parts = line.split('|').map((c) => c.trim());
        if (parts[0] === '') parts.shift();
        if (parts[parts.length - 1] === '') parts.pop();
        return parts;
      });
    } else {
      rows = lines.map((line) => [line]);
    }
    const colCount = Math.max(...rows.map((r) => r.length));
    const normalized = rows.map((r) => Array.from({ length: colCount }, (_, i) => r[i] ?? ''));
    return { _userEntered: true, title: 'Tablo', rows: normalized };
  }

  function renderTableFromRows(rows, headerRows) {
    if (!rows || !rows.length) return '';
    const hasMerge = rows.some((row) => row.some((c) => typeof c === 'object' && c !== null));
    if (!hasMerge) {
      const [header, ...body] = rows;
      const colCount = header.length;
      return `
        <table>
          <thead><tr>${header.map((c) => `<th style="text-align:center">${escapeHtml(toTitleCase(String(c)))}</th>`).join('')}</tr></thead>
          <tbody>${body.map((row) => `<tr>${Array.from({ length: colCount }, (_, i) => { const cell = row[i] || ''; return `<td style="text-align:${i === 0 ? 'left' : 'center'}">${escapeHtml(String(cell))}</td>`; }).join('')}</tr>`).join('')}</tbody>
        </table>
      `;
    }
    const numHead = headerRows || 1;
    const headRows = rows.slice(0, numHead);
    const bodyRows = rows.slice(numHead);
    const span = {}; // sütun → kalan rowspan sayısı (head+body arasında paylaşılır)
    function renderMergedSection(sectionRows, isHeader) {
      return sectionRows.map((row) => {
        const cells = [];
        let col = 0;
        row.forEach((cell) => {
          while ((span[col] || 0) > 0) col++;
          const colspan = cell.colspan || 1;
          const rowspan = cell.rowspan || 1;
          const cs = colspan > 1 ? ` colspan="${colspan}"` : '';
          const rs = rowspan > 1 ? ` rowspan="${rowspan}"` : '';
          const align = isHeader ? 'center' : (col === 0 ? 'left' : 'center');
          const vAlign = rowspan > 1 ? ';vertical-align:middle' : '';
          const tag = isHeader ? 'th' : 'td';
          const cellText = isHeader ? toTitleCase(cell.text) : cell.text;
          cells.push(`<${tag}${cs}${rs} style="text-align:${align}${vAlign}">${escapeHtml(cellText)}</${tag}>`);
          for (let c = 0; c < colspan; c++) span[col + c] = rowspan;
          col += colspan;
        });
        Object.keys(span).forEach((k) => { if (span[k] > 0) span[k]--; else delete span[k]; });
        return `<tr>${cells.join('')}</tr>`;
      }).join('');
    }
    return `
      <table>
        ${headRows.length ? `<thead>${renderMergedSection(headRows, true)}</thead>` : ''}
        ${bodyRows.length ? `<tbody>${renderMergedSection(bodyRows, false)}</tbody>` : ''}
      </table>
    `;
  }

  function updateMergeTablePreview(table) {
    const preview = document.getElementById('table-preview');
    if (!preview) return;
    preview.innerHTML = `<div class="structured-table"><div class="table-wrap">${renderTableFromRows(table.rows, table.headerRows)}</div></div>`;
  }

  function updateTablePreview(text) {
    const preview = document.getElementById('table-preview');
    if (!preview) return;
    const parsed = tsvToStructuredTable(text);
    preview.innerHTML = parsed ? `<div class="structured-table"><div class="table-wrap">${renderTableFromRows(parsed.rows)}</div></div>` : '';
  }

  function statusBadge(status) {
    const ok = ['KBY_APPROVED', 'KOB_READY', 'NO_CONTENT', 'PUBLISHED', 'KILITLI'].includes(status);
    const warn = ['DBY_REVIEW', 'DB_APPROVAL', 'KBY_APPROVAL', 'KOB_REVIEW', 'CHAIR_APPROVAL'].includes(status);
    const className = ok ? 'ok' : warn ? 'warn' : '';
    return `<span class="badge ${className}">${STATUS_LABELS[status] || status}</span>`;
  }

  function userName(userId) {
    return state.users.find((item) => item.id === userId)?.fullName || '';
  }

  function userNameFromState(sourceState, userId) {
    return sourceState.users.find((item) => item.id === userId)?.fullName || '';
  }

  function activateTab(view) {
    document.querySelectorAll('.tab').forEach((tab) => tab.classList.toggle('active', tab.dataset.view === view));
  }

  function getWeekNumber(date) {
    const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNumber = target.getUTCDay() || 7;
    target.setUTCDate(target.getUTCDate() + 4 - dayNumber);
    const yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
    return Math.ceil((((target - yearStart) / 86400000) + 1) / 7);
  }

  function hashString(value) {
    let hash = 0;
    for (let index = 0; index < value.length; index += 1) {
      hash = ((hash << 5) - hash) + value.charCodeAt(index);
      hash |= 0;
    }
    return `h${Math.abs(hash)}`;
  }

  function makeSearchKeywords(bulletinId) {
    return state.sections
      .filter((section) => section.bulletinId === bulletinId)
      .map((section) => `${section.title} ${section.contentHtml} ${section.departmentName}`)
      .join(' ')
      .toLowerCase();
  }

  window.HaftalikBultenApp = {
    getState: () => state,
    editUser: (userId) => {
      if (!isAdmin()) {
        alert('Bu işlem sadece admin kullanıcı tarafından yapılabilir.');
        return;
      }
      selectUserForEditing(userId);
    },
    createUser: (roleCode, departmentId) => {
      if (!isAdmin()) {
        alert('Bu işlem sadece admin kullanıcı tarafından yapılabilir.');
        return;
      }
      const item = createEditableUser(roleCode, departmentId || null);
      render();
      setTimeout(() => selectUserForEditing(item.id), 0);
    },
    reset: () => {
      state = seedState();
      persist();
      render();
    },
    printArchiveView: (archiveId, viewType) => printArchiveView(archiveId, viewType)
  };

  boot();
}());
