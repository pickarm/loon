// pickarm/loon - Loon region availability guard
//
// Loon does not expose an API to remove policy-group entries at runtime.
// This guard therefore enforces the practical equivalent: if a region has no
// nodes, it is treated as unavailable; any business policy currently selecting
// that empty region is automatically moved back to 兜底后备策略.

(function () {
  var REGIONS = [
    { name: "香港", probe: "香港手动策略", aliases: ["香港手动策略", "香港时延优选"] },
    { name: "台湾", probe: "台湾手动策略", aliases: ["台湾手动策略", "台湾时延优选"] },
    { name: "日本", probe: "日本手动策略", aliases: ["日本手动策略", "日本时延优选"] },
    { name: "韩国", probe: "韩国手动策略", aliases: ["韩国手动策略", "韩国时延优选"] },
    { name: "新加坡", probe: "新加坡手动策略", aliases: ["新加坡手动策略", "新加坡时延优选"] },
    { name: "美国", probe: "美国手动策略", aliases: ["美国手动策略", "美国时延优选"] },
    { name: "游戏", probe: "游戏手动策略", aliases: ["游戏手动策略"] }
  ];

  var BUSINESS_GROUPS = [
    "🤖 AI平台",
    "📲 电报消息",
    "📹 油管视频",
    "🎥 奈飞视频",
    "🌍 国外媒体",
    "Ⓜ️ 微软服务",
    "🍎 苹果服务",
    "🎮 游戏平台",
    "🌐 国外网站"
  ];

  var FALLBACK = "兜底后备策略";
  var pending = REGIONS.length;
  var unavailable = {};
  var completed = false;

  function safeDone() {
    if (completed) return;
    completed = true;
    $done();
  }

  function finishRegionScan() {
    pending -= 1;
    if (pending > 0 || completed) return;

    var unavailableNames = [];
    var invalidPolicies = {};

    REGIONS.forEach(function (region) {
      if (!unavailable[region.name]) return;
      unavailableNames.push(region.name);
      region.aliases.forEach(function (policy) {
        invalidPolicies[policy] = true;
      });
    });

    var changed = [];
    BUSINESS_GROUPS.forEach(function (group) {
      try {
        var selected = $config.getSelectedPolicy(group);
        if (selected && invalidPolicies[selected]) {
          if ($config.setSelectPolicy(group, FALLBACK)) {
            changed.push(group + ": " + selected + " → " + FALLBACK);
          }
        }
      } catch (e) {
        console.log("[region-guard] inspect failed: " + group + ": " + e);
      }
    });

    var state = unavailableNames.sort().join(",");
    var oldState = $persistentStore.read("region_guard_unavailable") || "";
    if (state !== oldState) {
      $persistentStore.write(state, "region_guard_unavailable");
      if (unavailableNames.length) {
        $notification.post(
          "Loon 地区节点检查",
          "已忽略空地区：" + unavailableNames.join(" / "),
          changed.length ? changed.join("\n") : "空地区不会参与有效业务选择。"
        );
      }
    }

    if (changed.length) {
      console.log("[region-guard] reset policies: " + changed.join(" | "));
    }
    console.log("[region-guard] unavailable: " + (state || "none"));
    safeDone();
  }

  REGIONS.forEach(function (region) {
    try {
      $config.getSubPolicies(region.probe, function (text) {
        var policies = [];
        try {
          policies = text ? JSON.parse(text) : [];
          if (!Array.isArray(policies)) policies = [];
        } catch (e) {
          policies = [];
        }
        unavailable[region.name] = policies.length === 0;
        finishRegionScan();
      });
    } catch (e) {
      unavailable[region.name] = true;
      finishRegionScan();
    }
  });

  // Older Loon builds may not callback for an invalid policy name.
  setTimeout(function () {
    if (!completed && pending > 0) {
      console.log("[region-guard] timeout while scanning region groups");
      safeDone();
    }
  }, 8000);
})();
