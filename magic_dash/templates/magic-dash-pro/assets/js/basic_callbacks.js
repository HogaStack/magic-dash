// 改造console.error()以隐藏无关痛痒的警告信息
const originalConsoleError = console.error;
console.error = function (...args) {
    // 检查args中是否包含需要过滤的内容
    const shouldFilter = args.some(arg => typeof arg === 'string' && arg.includes('Warning:'));

    if (!shouldFilter) {
        originalConsoleError.apply(console, args);
    }
};

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside_basic: {
        // 处理核心页面侧边栏展开/收起
        handleSideCollapse: (nClicks, originIcon, originHeaderSideStyle, coreConfig) => {
            // 若先前为展开状态
            if (originIcon === 'antd-menu-fold') {
                return [
                    // 更新图标
                    'antd-menu-unfold',
                    // 更新页首侧边容器样式
                    {
                        ...originHeaderSideStyle,
                        width: 110
                    },
                    // 更新页首标题样式
                    {
                        display: 'none'
                    },
                    // 更新侧边菜单容器样式
                    {
                        width: 110
                    },
                    // 更新侧边菜单折叠状态
                    true
                ]
            } else {
                return [
                    // 更新图标
                    'antd-menu-fold',
                    // 更新页首侧边容器样式
                    {
                        ...originHeaderSideStyle,
                        width: coreConfig.core_side_width
                    },
                    // 更新页首标题样式
                    {},
                    // 更新侧边菜单容器样式
                    {
                        width: coreConfig.core_side_width
                    },
                    // 更新侧边菜单折叠状态
                    false
                ]
            }
        },
        // 控制页面搜索切换页面的功能
        handleCorePageSearch: (value) => {
            if (value) {
                let pathname = value.split('|')[0]
                // 更新pathname
                window.location.pathname = pathname
            }
        },
        // 控制ctrl+k快捷键触发页面搜索框聚焦
        handleCorePageSearchFocus: (pressedCounts) => {
            return [true, pressedCounts.toString()]
        },
        // 处理多标签页形式下的标签页关闭操作
        handleCoreTabsClose: (tabCloseCounts, clickedContextMenu, latestDeletePane, items) => {
            // 获取本次回调触发来源信息
            callbackTriggered = window.dash_clientside.callback_context.triggered[0];

            // 若本次回调由标签页标题右键菜单操作触发
            if (callbackTriggered.prop_id.endsWith('clickedContextMenu')) {
                if (clickedContextMenu.menuKey === '关闭当前') {
                    // 计算下一状态对应标签页子项列表
                    let next_items = items.filter(item => item.key !== clickedContextMenu.tabKey);

                    return [
                        next_items,
                        // 默认在下一状态选中末尾的有效标签页
                        next_items[next_items.length - 1].key
                    ];
                } else if (clickedContextMenu.menuKey === '关闭其他') {
                    // 计算下一状态对应标签页子项列表
                    let next_items = items.filter(item => (item.key === clickedContextMenu.tabKey) || (item.key === '/'));

                    return [
                        next_items,
                        // 下一状态激活当前触发源标签页
                        clickedContextMenu.tabKey
                    ];
                } else if (clickedContextMenu.menuKey == '关闭所有') {
                    // 计算下一状态对应标签页子项列表
                    let next_items = items.filter(item => item.key === '/');

                    return [
                        next_items,
                        // 下一状态激活首页标签页
                        '/'
                    ];
                } else if (clickedContextMenu.menuKey === '刷新页面') {

                    // 触发页面刷新
                    window.dash_clientside.set_props(
                        'global-reload',
                        {
                            reload: true
                        }
                    )

                    return window.dash_clientside.no_update;
                }
            }

            // 否则，则本次回调由标签页关闭按钮触发
            // 计算下一状态对应标签页子项列表
            let next_items = items.filter(item => item.key !== latestDeletePane);

            return [
                next_items,
                // 默认在下一状态选中末尾的有效标签页
                next_items[next_items.length - 1].key
            ];
        },
        handleCoreFullscreenToggle: (nClicks, isFullscreen, icon) => {

            let _isFullscreen;

            if (window.dash_clientside.callback_context.triggered_id === 'core-fullscreen') {
                _isFullscreen = isFullscreen
            } else {
                _isFullscreen = icon === 'antd-full-screen'
            }

            return (
                _isFullscreen ?
                    [true, 'antd-full-screen-exit'] :
                    [false, 'antd-full-screen']
            )
        },
        // 使用Web Crypto API加密密码
        encryptPassword: async (password, publicKeyPem) => {
            if (!password || !publicKeyPem) {
                return null;
            }

            // 将PEM格式的公钥转换为ArrayBuffer
            const pemHeader = '-----BEGIN PUBLIC KEY-----';
            const pemFooter = '-----END PUBLIC KEY-----';
            const pemContents = publicKeyPem
                .replace(pemHeader, '')
                .replace(pemFooter, '')
                .replace(/\s/g, '');

            const binaryString = window.atob(pemContents);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            // 导入公钥
            const publicKey = await window.crypto.subtle.importKey(
                'spki',
                bytes.buffer,
                {
                    name: 'RSA-OAEP',
                    hash: 'SHA-256'
                },
                false,
                ['encrypt']
            );

            // 加密密码
            const encoder = new TextEncoder();
            const passwordData = encoder.encode(password);

            const encryptedData = await window.crypto.subtle.encrypt(
                {
                    name: 'RSA-OAEP'
                },
                publicKey,
                passwordData
            );

            // 将加密后的数据转换为Base64字符串
            const encryptedBytes = new Uint8Array(encryptedData);
            let binary = '';
            for (let i = 0; i < encryptedBytes.byteLength; i++) {
                binary += String.fromCharCode(encryptedBytes[i]);
            }
            const encryptedBase64 = window.btoa(binary);

            return encryptedBase64;
        }
    }
});