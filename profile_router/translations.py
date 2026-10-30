"""Japanese and English for every Chinese UI string passed to i18n.t(). Keys keep their {placeholders}."""

CATALOG: dict[str, dict[str, str]] = {
    # --- shared pieces ---------------------------------------------------------------------------
    "{name}（{browser}）": {"ja": "{name}（{browser}）", "en": "{name} ({browser})"},
    "、": {"ja": "、", "en": ", "},
    "账号": {"ja": "アカウント", "en": "Accounts"},
    "房间": {"ja": "ルーム", "en": "Rooms"},
    "打开": {"ja": "開く", "en": "Open"},
    "取消": {"ja": "キャンセル", "en": "Cancel"},
    "保存": {"ja": "保存", "en": "Save"},
    "添加": {"ja": "追加", "en": "Add"},
    "删除": {"ja": "削除", "en": "Delete"},
    "删除…": {"ja": "削除…", "en": "Delete…"},
    "创建": {"ja": "作成", "en": "Create"},
    "（找不到）": {"ja": "（見つかりません）", "en": "(not found)"},
    "设置": {"ja": "設定", "en": "Settings"},
    "浏览器": {"ja": "ブラウザー", "en": "Browser"},
    "新房间": {"ja": "新しいルーム", "en": "New room"},
    "新建房间": {"ja": "新しいルーム", "en": "New room"},
    "房间名": {"ja": "ルーム名", "en": "Room name"},
    "房间 {n}": {"ja": "ルーム {n}", "en": "Room {n}"},
    "房间：{room}": {"ja": "ルーム：{room}", "en": "Room: {room}"},
    "还没有账号": {"ja": "アカウントはまだありません", "en": "No accounts yet"},

    # --- delete rules ----------------------------------------------------------------------------
    "只能删除 Chrome、Edge 等 Chromium 系浏览器的房间": {
        "ja": "削除できるのは Chrome、Edge など Chromium 系ブラウザーのルームだけです",
        "en": "Only rooms of Chromium-based browsers (Chrome, Edge, …) can be deleted"},
    "这是浏览器的主房间，不能删除": {
        "ja": "ブラウザーのメインルームなので削除できません",
        "en": "This is the browser's main room and can't be deleted"},
    "登录着浏览器账号 {account}，不能删除": {
        "ja": "ブラウザーのアカウント {account} でサインイン中のため削除できません",
        "en": "Signed in to the browser account {account}; can't be deleted"},
    "还登记着 {n} 个网站账号，请先在「房间设置」里删除这些账号": {
        "ja": "サイトのアカウントが {n} 件登録されています。先に「ルーム設定」で削除してください",
        "en": "{n} site account(s) still registered; delete them in \"Room settings\" first"},

    # --- extension picker ------------------------------------------------------------------------
    "扩展，复制自": {"ja": "拡張機能のコピー元", "en": "Copy extensions from"},
    "全不选": {"ja": "すべて解除", "en": "None"},
    "全选": {"ja": "すべて選択", "en": "All"},
    "这个房间没有可复制的扩展": {
        "ja": "このルームにはコピーできる拡張機能がありません",
        "en": "This room has no extensions to copy"},
    "{name}（已停用）  · 密码管理器": {
        "ja": "{name}（無効）  · パスワードマネージャー", "en": "{name} (disabled)  · password manager"},
    "{name}  · 密码管理器": {"ja": "{name}  · パスワードマネージャー", "en": "{name}  · password manager"},
    "{name}（已停用）": {"ja": "{name}（無効）", "en": "{name} (disabled)"},

    # --- main window -----------------------------------------------------------------------------
    "浏览器账号切换": {"ja": "ブラウザーアカウント切り替え", "en": "Browser Account Switcher"},
    "⚙ 设置": {"ja": "⚙ 設定", "en": "⚙ Settings"},
    "搜索网站或账号，或粘贴网址回车": {
        "ja": "サイトやアカウントを検索、または URL を貼り付けて Enter",
        "en": "Search sites or accounts, or paste a URL and press Enter"},
    "已同步：新房间 {names}": {"ja": "同期しました：新しいルーム {names}", "en": "Synced: new room {names}"},
    "已同步浏览器里的变化": {"ja": "ブラウザーの変更を同期しました", "en": "Synced changes from the browsers"},
    "已同步": {"ja": "同期しました", "en": "Synced"},
    "{sites} 个网站 · {accounts} 个账号 · {rooms} 个房间": {
        "ja": "サイト {sites} · アカウント {accounts} · ルーム {rooms}",
        "en": "Sites: {sites} · Accounts: {accounts} · Rooms: {rooms}"},

    # --- accounts page ---------------------------------------------------------------------------
    "还没有账号。\n① 在下面添加一个网站（如 x.com）\n② 点那一行的「＋」给它加账号，选一个房间或新建房间，在打开的页面里登录一次": {
        "ja": "アカウントはまだありません。\n① 下でサイトを追加します（例：x.com）\n"
              "② その行の「＋」でアカウントを追加し、ルームを選ぶか新しく作って、開いたページで一度ログインします",
        "en": "No accounts yet.\n① Add a site below (e.g. x.com)\n"
              "② Click \"＋\" on its row to add an account, pick a room or create one, and log in once on the page that opens"},
    "没有匹配「{q}」的网站或账号；回车可当网址打开。": {
        "ja": "「{q}」に一致するサイトやアカウントはありません。Enter で URL として開けます。",
        "en": "No site or account matches \"{q}\"; press Enter to open it as a URL."},
    "＋ 添加网站": {"ja": "＋ サイトを追加", "en": "＋ Add site"},
    "输入网址，会自动获取网站图标": {
        "ja": "URL を入力するとサイトのアイコンを自動で取得します",
        "en": "Enter a URL; the site icon is fetched automatically"},
    "添加账号…": {"ja": "アカウントを追加…", "en": "Add account…"},
    "重新获取图标": {"ja": "アイコンを再取得", "en": "Fetch icon again"},
    "移除这个网站…": {"ja": "このサイトを削除…", "en": "Remove this site…"},
    "{site} · {label}  →  房间「{room}」 · 打开 {n} 个常用页": {
        "ja": "{site} · {label}  →  ルーム「{room}」 · よく使うページを {n} 件開く",
        "en": "{site} · {label}  →  room \"{room}\" · opens {n} pinned page(s)"},
    "{site} · {label}  →  房间「{room}」": {
        "ja": "{site} · {label}  →  ルーム「{room}」", "en": "{site} · {label}  →  room \"{room}\""},
    "常用页…（{n}）": {"ja": "よく使うページ…（{n}）", "en": "Pinned pages… ({n})"},
    "常用页…": {"ja": "よく使うページ…", "en": "Pinned pages…"},
    "创建快捷方式…": {"ja": "ショートカットを作成…", "en": "Create shortcut…"},
    "改名…": {"ja": "名前を変更…", "en": "Rename…"},
    "{room}（当前）": {"ja": "{room}（現在）", "en": "{room} (current)"},
    "{room}（已有 {label}）": {"ja": "{room}（{label} あり）", "en": "{room} (has {label})"},
    "移到房间": {"ja": "ルームを移動", "en": "Move to room"},
    "删除这个账号": {"ja": "このアカウントを削除", "en": "Delete this account"},
    "切换账号": {"ja": "アカウント切り替え", "en": "Switch account"},
    "找不到「{label}」所在的房间（{card}）。": {
        "ja": "「{label}」のルーム（{card}）が見つかりません。",
        "en": "Can't find the room of \"{label}\" ({card})."},
    "已切到 {site} · {label}（房间「{room}」），打开了 {n} 个常用页": {
        "ja": "{site} · {label} に切り替えました（ルーム「{room}」）。よく使うページを {n} 件開きました",
        "en": "Switched to {site} · {label} (room \"{room}\"), opened {n} pinned page(s)"},
    "已切到 {site} · {label}（房间「{room}」）": {
        "ja": "{site} · {label} に切り替えました（ルーム「{room}」）",
        "en": "Switched to {site} · {label} (room \"{room}\")"},
    "用房间「{room}」打开": {"ja": "ルーム「{room}」で開きました", "en": "Opened in room \"{room}\""},
    "已添加 {site}，正在获取图标…": {
        "ja": "{site} を追加しました。アイコンを取得中…", "en": "Added {site}, fetching its icon…"},
    "移除网站": {"ja": "サイトを削除", "en": "Remove site"},
    "移除 {site}？": {"ja": "{site} を削除しますか？", "en": "Remove {site}?"},
    "改名": {"ja": "名前を変更", "en": "Rename"},
    "{site} 的账号名：": {"ja": "{site} のアカウント名：", "en": "Account name on {site}:"},
    "把 {site} · {label} 登记到房间「{room}」？\n只改登记；那个房间里还要登录一次这个账号。": {
        "ja": "{site} · {label} をルーム「{room}」に登録しますか？\n"
              "登録を変えるだけです。そのルームでこのアカウントに一度ログインしてください。",
        "en": "Register {site} · {label} in room \"{room}\"?\n"
              "This only changes the record; you still need to log in to this account once in that room."},

    # --- rooms page ------------------------------------------------------------------------------
    "＋ 新建房间": {"ja": "＋ 新しいルーム", "en": "＋ New room"},
    "收起已隐藏的 {n} 个房间": {"ja": "非表示のルーム {n} 件をたたむ", "en": "Collapse {n} hidden room(s)"},
    "显示已隐藏的 {n} 个房间": {"ja": "非表示のルーム {n} 件を表示", "en": "Show {n} hidden room(s)"},
    "恢复": {"ja": "再表示", "en": "Restore"},
    "打开这个房间": {"ja": "このルームを開く", "en": "Open this room"},
    "房间设置（名字、颜色、账号）…": {
        "ja": "ルーム設定（名前・色・アカウント）…", "en": "Room settings (name, color, accounts)…"},
    "复制扩展到这个房间…": {"ja": "このルームに拡張機能をコピー…", "en": "Copy extensions to this room…"},
    "从列表隐藏": {"ja": "一覧から隠す", "en": "Hide from list"},
    "删除这个房间…": {"ja": "このルームを削除…", "en": "Delete this room…"},
    "删除这个房间（{reason}）": {"ja": "このルームを削除（{reason}）", "en": "Delete this room ({reason})"},
    "已打开房间「{room}」": {"ja": "ルーム「{room}」を開きました", "en": "Opened room \"{room}\""},
    "删除房间": {"ja": "ルームを削除", "en": "Delete room"},
    "请先关闭 {browser} 的所有窗口，再删除房间。\n浏览器开着时删除，它可能把这个用户又写回去。": {
        "ja": "{browser} のウィンドウをすべて閉じてから削除してください。\n"
              "ブラウザーが開いていると、このユーザーが書き戻されることがあります。",
        "en": "Close all {browser} windows before deleting the room.\n"
              "If the browser is open, it may write this profile back."},
    "删除房间「{name}」（{browser}）？\n\n这个浏览器用户的文件夹（书签、扩展、浏览记录、登录状态）会移到回收站，需要时可以从回收站还原。": {
        "ja": "ルーム「{name}」（{browser}）を削除しますか？\n\n"
              "このブラウザーユーザーのフォルダー（ブックマーク、拡張機能、閲覧履歴、ログイン状態）はごみ箱に移動します。"
              "必要ならごみ箱から元に戻せます。",
        "en": "Delete room \"{name}\" ({browser})?\n\n"
              "This browser profile's folder (bookmarks, extensions, history, logins) will be moved to the Recycle Bin, "
              "where you can restore it if needed."},
    "已删除房间「{name}」，文件夹在回收站里": {
        "ja": "ルーム「{name}」を削除しました。フォルダーはごみ箱にあります",
        "en": "Deleted room \"{name}\"; its folder is in the Recycle Bin"},
    "没有找到可新建用户的浏览器（支持 Chrome、Edge、Brave、Vivaldi、Iron）。": {
        "ja": "ユーザーを作成できるブラウザーが見つかりません（対応：Chrome、Edge、Brave、Vivaldi、Iron）。",
        "en": "No browser that can create profiles was found (supported: Chrome, Edge, Brave, Vivaldi, Iron)."},

    # --- new room / add account ------------------------------------------------------------------
    "新房间是本地用户，不会弹出浏览器的登录、设置页面；勾选的扩展会打开商店页，点一下「添加」。Windows Hello 里的通行密钥所有房间都能直接用。": {
        "ja": "新しいルームはローカルユーザーなので、ブラウザーのログインや設定ページは開きません。"
              "チェックした拡張機能はストアページが開くので「追加」を押してください。"
              "Windows Hello のパスキーはどのルームでもそのまま使えます。",
        "en": "A new room is a local profile, so no browser sign-in or setup pages pop up. Each checked extension "
              "opens its store page; click \"Add\" there. Passkeys in Windows Hello work in every room."},
    "给 {site} 添加账号": {"ja": "{site} にアカウントを追加", "en": "Add an account to {site}"},
    "账号名": {"ja": "アカウント名", "en": "Account name"},
    "自己认得出就行，如「小号」": {"ja": "自分で分かれば OK（例：「サブ」）", "en": "Anything you'll recognize, e.g. \"alt\""},
    "放在哪个房间里：": {"ja": "どのルームに入れますか：", "en": "Which room should it live in:"},
    "已有 {site} {label}，同一房间不能放同网站两个账号": {
        "ja": "{site} {label} があります。1 つのルームに同じサイトのアカウントは 2 つ置けません",
        "en": "Already has {site} {label}; a room holds only one account per site"},
    "已有：{accounts}": {"ja": "登録済み：{accounts}", "en": "Has: {accounts}"},
    "空房间": {"ja": "空のルーム", "en": "Empty room"},
    "添加并打开登录页": {"ja": "追加してログインページを開く", "en": "Add and open login page"},
    "添加账号": {"ja": "アカウントを追加", "en": "Add account"},
    "请填写账号名，并选择房间。": {
        "ja": "アカウント名を入力し、ルームを選んでください。", "en": "Enter an account name and choose a room."},
    "已添加 {site} · {label}，请在打开的页面里登录": {
        "ja": "{site} · {label} を追加しました。開いたページでログインしてください",
        "en": "Added {site} · {label}; log in on the page that opened"},
    "创建并打开": {"ja": "作成して開く", "en": "Create and open"},
    "已新建房间「{name}」": {"ja": "ルーム「{name}」を作成しました", "en": "Created room \"{name}\""},
    "复制扩展到「{room}」": {"ja": "「{room}」に拡張機能をコピー", "en": "Copy extensions to \"{room}\""},
    "会在这个房间里打开勾选扩展的商店页，每个点一下「添加」。": {
        "ja": "このルームでチェックした拡張機能のストアページを開きます。それぞれ「追加」を押してください。",
        "en": "Opens the store page of each checked extension in this room; click \"Add\" on each."},
    "打开商店页": {"ja": "ストアページを開く", "en": "Open store pages"},

    # --- pinned pages ----------------------------------------------------------------------------
    "{site} · {label} 的常用页": {"ja": "{site} · {label} のよく使うページ", "en": "Pinned pages of {site} · {label}"},
    "切到「{label}」时，这些页面会在它的房间里一起打开；没有常用页时打开网站首页。": {
        "ja": "「{label}」に切り替えると、これらのページがそのルームでまとめて開きます。"
              "よく使うページがなければサイトのトップページを開きます。",
        "en": "Switching to \"{label}\" opens these pages together in its room; with none, the site's home page opens."},
    "上移": {"ja": "上へ", "en": "Up"},
    "下移": {"ja": "下へ", "en": "Down"},

    # --- shortcuts -------------------------------------------------------------------------------
    "账号：{site} · {label}（房间「{room}」）": {
        "ja": "アカウント：{site} · {label}（ルーム「{room}」）",
        "en": "Account: {site} · {label} (room \"{room}\")"},
    "房间：{room}（{browser}）": {"ja": "ルーム：{room}（{browser}）", "en": "Room: {room} ({browser})"},
    "创建快捷方式": {"ja": "ショートカットを作成", "en": "Create shortcut"},
    "启动项": {"ja": "起動対象", "en": "Opens"},
    "名称": {"ja": "名前", "en": "Name"},
    "生成在": {"ja": "作成場所", "en": "Create in"},
    "会打开：{urls}": {"ja": "開くページ：{urls}", "en": "Opens: {urls}"},
    "只打开这个房间": {"ja": "このルームだけを開きます", "en": "Opens just this room"},
    "请选择生成在哪里。": {"ja": "作成場所を選んでください。", "en": "Choose where to create it."},
    "快捷方式": {"ja": "ショートカット", "en": "Shortcut"},
    "已创建快捷方式「{name}」：{places}": {
        "ja": "ショートカット「{name}」を作成しました：{places}", "en": "Created shortcut \"{name}\": {places}"},
    "桌面": {"ja": "デスクトップ", "en": "Desktop"},
    "开始菜单": {"ja": "スタートメニュー", "en": "Start menu"},
    "创建快捷方式失败": {"ja": "ショートカットを作成できませんでした", "en": "Failed to create the shortcut"},

    # --- room settings ---------------------------------------------------------------------------
    "房间设置": {"ja": "ルーム設定", "en": "Room settings"},
    "打开时的网址": {"ja": "開くときの URL", "en": "Start page"},
    "颜色": {"ja": "色", "en": "Color"},
    "选择…": {"ja": "選択…", "en": "Choose…"},
    "这个房间里的账号": {"ja": "このルームのアカウント", "en": "Accounts in this room"},
    "没有账号。现在可以在「房间」页的「⋯」里删除这个房间（主房间除外）。": {
        "ja": "アカウントはありません。「ルーム」ページの「⋯」からこのルームを削除できます（メインルームを除く）。",
        "en": "No accounts. You can now delete this room from \"⋯\" on the Rooms page (except main rooms)."},

    # --- delete accounts -------------------------------------------------------------------------
    "移除网站 {site}": {"ja": "サイト {site} を削除", "en": "Remove site {site}"},
    "删除账号 {site} · {label}": {"ja": "アカウント {site} · {label} を削除", "en": "Delete account {site} · {label}"},
    "· {site} · {label}（房间「{room}」）": {
        "ja": "· {site} · {label}（ルーム「{room}」）", "en": "· {site} · {label} (room \"{room}\")"},
    "要删除的账号：\n{lines}": {"ja": "削除するアカウント：\n{lines}", "en": "Accounts to delete:\n{lines}"},
    "⚠ 删除账号会同时删除这个网站在该房间里的登录 Cookie、网站数据和权限设置，这个房间会退出该账号，无法恢复。下次要用得重新登录。": {
        "ja": "⚠ アカウントを削除すると、このルームにあるこのサイトのログイン Cookie、サイトデータ、権限設定も削除され、"
              "このルームはそのアカウントからログアウトします。元に戻せません。次に使うときは再ログインが必要です。",
        "en": "⚠ Deleting an account also deletes this site's login Cookies, site data and permissions in that room, "
              "so the room is logged out of it. This can't be undone; you'll need to log in again next time."},
    "清除登录 Cookie 和网站数据（取消勾选则只删登记，浏览器里保持登录）": {
        "ja": "ログイン Cookie とサイトデータを消去（チェックを外すと登録だけ削除し、ブラウザーではログインしたまま）",
        "en": "Clear login Cookies and site data (uncheck to only remove the record and stay logged in)"},
    "在浏览器里删…": {"ja": "ブラウザーで削除…", "en": "Delete in browser…"},
    "网站设置": {"ja": "サイトの設定", "en": "Site settings"},
    "已打开房间「{room}」，并复制了 {site} 的网站设置页地址。\n\n在地址栏粘贴（Ctrl+V）回车，点「删除数据」即可退出登录。\n删完回来点「删除」，并取消勾选清除（已经清过了）。": {
        "ja": "ルーム「{room}」を開き、{site} のサイト設定ページのアドレスをコピーしました。\n\n"
              "アドレスバーに貼り付けて（Ctrl+V）Enter を押し、「データを削除」を押すとログアウトします。\n"
              "削除したら戻って「削除」を押し、消去のチェックは外してください（すでに消去済みです）。",
        "en": "Opened room \"{room}\" and copied the address of {site}'s site settings page.\n\n"
              "Paste it in the address bar (Ctrl+V), press Enter and click \"Delete data\" to log out.\n"
              "Then come back, click \"Delete\" and uncheck clearing (it's already done)."},
    "删除账号": {"ja": "アカウントを削除", "en": "Delete account"},
    "请先关闭 {browsers} 的所有窗口再删除——浏览器开着时登录数据被占用，删不掉。\n也可以点「在浏览器里删…」，在浏览器的网站设置页里删。": {
        "ja": "{browsers} のウィンドウをすべて閉じてから削除してください。ブラウザーが開いているとログインデータが使用中で削除できません。\n"
              "「ブラウザーで削除…」を押して、ブラウザーのサイト設定ページで削除することもできます。",
        "en": "Close all {browsers} windows first: while the browser is open its login data is locked and can't be deleted.\n"
              "Or click \"Delete in browser…\" to delete it on the browser's site settings page."},
    "清除 {site} 的数据时出错：{error}": {
        "ja": "{site} のデータを消去中にエラーが発生しました：{error}", "en": "Error clearing data of {site}: {error}"},
    "已删除 {names}，清除了 {n} 个 Cookie": {
        "ja": "{names} を削除し、Cookie を {n} 件消去しました", "en": "Deleted {names}, cleared {n} Cookie(s)"},
    "已删除 {names}（浏览器里仍保持登录）": {
        "ja": "{names} を削除しました（ブラウザーではログインしたままです）",
        "en": "Deleted {names} (still logged in in the browser)"},

    # --- settings --------------------------------------------------------------------------------
    "语言": {"ja": "言語", "en": "Language"},
    "跟随系统（{name}）": {"ja": "システムに合わせる（{name}）", "en": "Follow system ({name})"},
    "界面语言": {"ja": "表示言語", "en": "Display language"},
    "新的界面语言会在重新打开程序后生效。": {
        "ja": "新しい表示言語はアプリを再起動すると反映されます。",
        "en": "The new language takes effect after restarting the app."},
    "同步": {"ja": "同期", "en": "Sync"},
    "自动同步：浏览器里新建、删除、改名的用户，不用重启就会出现在「房间」里": {
        "ja": "自動同期：ブラウザーで追加・削除・名前変更したユーザーが、再起動なしで「ルーム」に反映されます",
        "en": "Auto sync: profiles added, deleted or renamed in the browsers show up in Rooms without a restart"},
    "立即同步": {"ja": "今すぐ同期", "en": "Sync now"},
    "说明：网站账号要在「账号」页登记（＋），程序不会读取浏览器里的登录信息。": {
        "ja": "注：サイトのアカウントは「アカウント」ページで登録します（＋）。ブラウザーのログイン情報は読み取りません。",
        "en": "Note: register site accounts on the Accounts page (＋); this app never reads login data from the browsers."},
    "链接": {"ja": "リンク", "en": "Links"},
    "设为默认浏览器后，从别的软件点开的链接也会送到对的账号。": {
        "ja": "既定のブラウザーにすると、ほかのアプリで開いたリンクも正しいアカウントに届きます。",
        "en": "As the default browser, links opened from other apps also go to the right account."},
    "设为默认浏览器…": {"ja": "既定のブラウザーにする…", "en": "Set as default browser…"},
    "打开没有登记账号的网站时：": {
        "ja": "アカウント未登録のサイトを開くとき：", "en": "When opening a site with no registered account:"},
    "弹窗让我选房间": {"ja": "ルームを選ぶ画面を出す", "en": "Ask me which room"},
    "总是用": {"ja": "常に使う", "en": "Always use"},
    "按域名指定房间（规则）…": {"ja": "ドメインごとにルームを指定（ルール）…", "en": "Room per domain (rules)…"},
    "新房间默认扩展": {"ja": "新しいルームの拡張機能", "en": "New room extensions"},
    "新建房间时默认勾选这些扩展。": {
        "ja": "新しいルームを作るとき、これらの拡張機能を最初からチェックします。",
        "en": "These extensions are checked by default when creating a new room."},
    "关于": {"ja": "情報", "en": "About"},
    "设置和图标保存在：{path}": {"ja": "設定とアイコンの保存先：{path}", "en": "Settings and icons are stored in: {path}"},
    "打开文件夹": {"ja": "フォルダーを開く", "en": "Open folder"},
    "设为默认浏览器": {"ja": "既定のブラウザーにする", "en": "Set as default browser"},
    "将在当前 Windows 用户下登记「Profile Router」为可选浏览器（只写 HKCU，可随时撤销）。\n\n登记后会打开 Windows 的「默认应用」设置，请在那里把 HTTP 和 HTTPS 改成 Profile Router。\n\n继续吗？": {
        "ja": "現在の Windows ユーザーに「Profile Router」を選択可能なブラウザーとして登録します（HKCU のみ、いつでも元に戻せます）。\n\n"
              "登録後に Windows の「既定のアプリ」設定が開くので、HTTP と HTTPS を Profile Router に変更してください。\n\n続けますか？",
        "en": "Profile Router will be registered as an available browser for the current Windows user "
              "(HKCU only, can be undone any time).\n\n"
              "Windows \"Default apps\" settings will then open; set HTTP and HTTPS to Profile Router there.\n\nContinue?"},

    # --- rules -----------------------------------------------------------------------------------
    "按域名指定房间": {"ja": "ドメインごとにルームを指定", "en": "Room per domain"},
    "网站没有登记账号时，按这里的规则选房间。github.com 也会匹配 gist.github.com；可以用 * 通配。": {
        "ja": "アカウント未登録のサイトは、ここのルールでルームを選びます。github.com は gist.github.com にも一致します。* をワイルドカードに使えます。",
        "en": "For sites with no registered account, these rules pick the room. github.com also matches "
              "gist.github.com; * works as a wildcard."},
    "域名": {"ja": "ドメイン", "en": "Domain"},
    "删除选中": {"ja": "選択を削除", "en": "Delete selected"},
    "{card}（未找到）": {"ja": "{card}（見つかりません）", "en": "{card} (not found)"},

    # --- picker ----------------------------------------------------------------------------------
    "用哪个房间打开？": {"ja": "どのルームで開きますか？", "en": "Open in which room?"},
    "用哪个账号打开？": {"ja": "どのアカウントで開きますか？", "en": "Open with which account?"},
    "以后 {host} 都用这个房间打开": {"ja": "今後 {host} は常にこのルームで開く", "en": "Always open {host} in this room"},
    "这个网站登记了多个账号：": {"ja": "このサイトには複数のアカウントが登録されています：",
                         "en": "This site has several registered accounts:"},

    # --- browsers.py -----------------------------------------------------------------------------
    "只能删除 Chromium 系浏览器的用户": {
        "ja": "削除できるのは Chromium 系ブラウザーのユーザーだけです",
        "en": "Only profiles of Chromium-based browsers can be deleted"},
    "没能把 {path} 移到回收站": {"ja": "{path} をごみ箱に移動できませんでした", "en": "Couldn't move {path} to the Recycle Bin"},
    "只能清除 Chromium 系浏览器的网站数据": {
        "ja": "サイトデータを消去できるのは Chromium 系ブラウザーだけです",
        "en": "Site data can only be cleared in Chromium-based browsers"},
}
