/*
 * 原型期统一健康分读取适配层。
 * 正式开发时由健康分服务接口替换 snapshots；页面只能通过本对象读取当前分数。
 */
(function () {
  const snapshots = Object.freeze({
    'EL-2024-019': { score: 82, updatedAt: '2026-07-12 14:20' },
    'EL-2023-088': { score: 68, updatedAt: '2026-07-12 14:20' },
    'EL-2022-031': { score: 72, updatedAt: '2026-07-12 14:20' },
    'EL-2024-102': { score: 87, updatedAt: '2026-07-12 14:20' },
    'EL-2025-006': { score: 91, updatedAt: '2026-07-12 14:20' },
    'EL-2021-047': { score: 58, updatedAt: '2026-07-12 14:20' },
    'EL-2024-211': { score: 76, updatedAt: '2026-07-12 14:20' },
    'EL-2023-156': { score: 83, updatedAt: '2026-07-12 14:20' },
    'EL-2022-204': { score: 64, updatedAt: '2026-07-12 14:20' },
    'EL-2025-018': { score: 89, updatedAt: '2026-07-12 14:20' },
    'EL-2026-003': { score: 93, updatedAt: '2026-07-12 14:20' },
    'EL-2022-309': { score: 69, updatedAt: '2026-07-12 14:20' },
    'EL-2024-105': { score: 100, updatedAt: '2026-07-12 14:20' },
    'EL-2023-062': { score: 76, updatedAt: '2026-07-12 14:20' },
    'EL-2024-076': { score: 86, updatedAt: '2026-07-12 14:20' },
    'EL-2022-044': { score: 54, updatedAt: '2026-07-12 14:20' },
    'EL-2024-122': { score: 61, updatedAt: '2026-07-12 14:20' },
    'EL-2022-209': { score: 45, updatedAt: '2026-07-12 14:20' },
    'ZL-2026-08': { score: 88, updatedAt: '2026-07-12 14:20' },
    'ZL-2026-07': { score: 73, updatedAt: '2026-07-12 14:20' },
    'ZL-2026-06': { score: 58, updatedAt: '2026-07-12 14:20' },
    'ZL-2026-05': { score: 36, updatedAt: '2026-07-12 14:20' },
    'ZL-2025-21': { score: 73, updatedAt: '2026-07-12 14:20' },
    'ZL-2024-15': { score: 58, updatedAt: '2026-07-12 14:20' },
    'ZL-2023-39': { score: 36, updatedAt: '2026-07-12 14:20' }
  });

  const riskClassMap = Object.freeze({
    '正常': 'normal',
    '低风险': 'low',
    '中风险': 'medium',
    '高风险': 'high',
    '严重风险': 'severe'
  });

  function getRisk(score) {
    if (score === 100) return '正常';
    if (score >= 80) return '低风险';
    if (score >= 60) return '中风险';
    if (score >= 40) return '高风险';
    return '严重风险';
  }

  function getEquipment(deviceId) {
    const snapshot = snapshots[deviceId];
    if (!snapshot) return null;
    const risk = getRisk(snapshot.score);
    return Object.freeze({
      id: deviceId,
      score: snapshot.score,
      risk,
      riskClass: riskClassMap[risk],
      updatedAt: snapshot.updatedAt
    });
  }

  function getDistribution(deviceIds) {
    const ids = Array.isArray(deviceIds) ? deviceIds : Object.keys(snapshots);
    return ids.reduce((distribution, deviceId) => {
      const item = getEquipment(deviceId);
      if (!item) return distribution;
      distribution[item.riskClass] += 1;
      return distribution;
    }, { normal: 0, low: 0, medium: 0, high: 0, severe: 0 });
  }

  window.HealthScoreService = Object.freeze({
    getEquipment,
    getDistribution,
    getRisk
  });
}());
