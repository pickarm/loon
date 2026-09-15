const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const source = fs.readFileSync('runtime/region_guard.js', 'utf8');

const regionNodes = {
  '香港手动策略': ['HK-01', 'HK-02'],
  '台湾手动策略': ['TW-01'],
  '日本手动策略': ['JP-01'],
  '韩国手动策略': [],
  '新加坡手动策略': ['SG-01'],
  '美国手动策略': ['US-01'],
  '游戏手动策略': []
};

const selected = {
  '🤖 AI平台': '韩国时延优选',
  '📲 电报消息': '新加坡时延优选',
  '📹 油管视频': '香港时延优选',
  '🎥 奈飞视频': '兜底后备策略',
  '🌍 国外媒体': '日本手动策略',
  'Ⓜ️ 微软服务': 'DIRECT',
  '🍎 苹果服务': 'DIRECT',
  '🎮 游戏平台': '游戏手动策略',
  '🌐 国外网站': '香港手动策略'
};

const writes = {};
let doneCount = 0;

const context = {
  console,
  JSON,
  Array,
  setTimeout: () => 1,
  $done: () => { doneCount += 1; },
  $notification: { post: () => {} },
  $persistentStore: {
    read: (key) => writes[key] || '',
    write: (value, key) => { writes[key] = value; return true; }
  },
  $config: {
    getSubPolicies: (group, cb) => cb(JSON.stringify(regionNodes[group] || [])),
    getSelectedPolicy: (group) => selected[group] || '',
    setSelectPolicy: (group, policy) => {
      selected[group] = policy;
      return true;
    }
  }
};

vm.runInNewContext(source, context, { filename: 'region_guard.js' });

assert.strictEqual(selected['🤖 AI平台'], '兜底后备策略', 'empty KR selection should fall back');
assert.strictEqual(selected['🎮 游戏平台'], '兜底后备策略', 'empty GAME selection should fall back');
assert.strictEqual(selected['📲 电报消息'], '新加坡时延优选', 'available SG selection should stay');
assert.strictEqual(selected['📹 油管视频'], '香港时延优选', 'available HK selection should stay');
assert.ok((writes.region_guard_unavailable || '').includes('韩国'), 'KR should be marked unavailable');
assert.ok((writes.region_guard_unavailable || '').includes('游戏'), 'GAME should be marked unavailable');
assert.strictEqual(doneCount, 1, '$done should be called exactly once');

console.log('region_guard.test.js: OK');
