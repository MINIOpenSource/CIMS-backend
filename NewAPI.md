:27041 Client API
  GET:/ 服务状态检测
  /api/v1/client
    GET:/{client_uid}/manifest 获取客户端清单
    GET:/{resource_type} 获取客户端资源
  GET:/get 令牌换取资源内容
  GET:/api/v1/management-config 获取引导配置

:27042 Management API
  GET:/ 服务状态检测
  /token
    POST:/refresh 刷新 Token
    POST:/verify 验证 Token
    POST:/deactivate 登出
  /user
    POST:/apply 申请注册
    POST:/auth 请求 Token (登录)
    GET:/info 获取用户信息
    /availability
      GET:/mail 检查邮箱可用性
      GET:/username 检查用户名可用性
    /2fa
      /totp
        POST:/enable 启用 TOTP
        POST:/confirm 确认绑定 TOTP
        POST:/disable 禁用 TOTP
        POST:/verify 验证 TOTP
        POST:/recover 恢复码登录
    /info
      GET:/ 获取用户信息
      POST:/email 修改邮箱
      POST:/username 修改用户名
      /password
        POST:/reset 重置密码
        POST:/change 修改密码
  /account
    GET:/list 列出所有账户
    POST:/search 搜索账户
    POST:/apply 申请创建新账户
    /availability
      GET:/slug 检查账户Slug可用性
    /{account_id}
      DELETE:/ 删除账户
      /info
        GET:/ 获取账户信息
        POST:/slug 修改账户 slug
      /{resource_type}
        GET:/list 列出资源
        POST:/search 搜索资源
        POST:/create 创建资源
        POST:/upload 上传资源
        /{resource_id}
          DELETE:/ 删除资源
          POST:/rename 重命名资源
          POST:/ 覆盖写入资源
          GET:/ 下载资源
      /client
        GET:/list 列出客户端
        GET:/search 搜索客户端
        /{client_id}
          DELETE:/ 删除客户端
          POST:/rename 重命名客户端
          GET:/status 获取客户端状态
          GET:/ 客户端详情
          POST:/disconnect 断开连接
          POST:/disable 禁用客户端
          POST:/enable 启用客户端
          POST:/config 修改客户端使用的档案组
          /command
            POST:/restart 重启客户端
            POST:/update-data 强制同步数据
            POST:/send-notification 发送通知
            GET:/get-config 获取运行时配置
      /pairing
        GET:/list 列出配对码
        GET:/search 搜索配对码
        /{pairing_id}
          POST:/reject 拒绝配对码
          POST:/approve 批准配对码
        POST:/enable 启用配对码
        POST:/disable 禁用配对码
      /pre-registration
        GET:/list 列出预注册客户端
        GET:/search 搜索预注册客户端
        /{pre_reg_id}
          DELETE:/ 删除预注册客户端
          POST:/rename 重命名预注册客户端
          GET:/ 获取预注册客户端信息
          POST:/enable 启用预注册客户端
          POST:/disable 禁用预注册客户端
          GET:/ManagementPreset.json 下载引导配置
          POST:/config 修改预注册客户端使用的档案组
      /access
        GET:/list 列出具权用户
        GET:/search 搜索具权用户
        /{user_id}
          DELETE:/ 删除具权用户
          POST:/rename 重命名具权用户
          GET:/ 获取具权用户信息
          POST:/ 修改具权用户的权限
      /invitation
        GET:/list 列出邀请列表
        POST:/create 创建邀请
        GET:/search 搜索邀请
        /{invitation_id}
          DELETE:/ 删除邀请
          POST:/rename 重命名邀请
          GET:/ 获取邀请信息
    /bulk
      POST:/ 批量操作

:27043 Admin API
  / 服务状态检测
  /user
    GET:/list 列出所有用户
    GET:/search 搜索用户
    POST:/create 创建用户
    /{user_id}
      DELETE:/ 删除用户
      POST:/rename 重命名用户
      GET:/ 获取用户信息
      POST:/ 修改用户信息
      /password
        POST:/reset 重置密码
        POST:/change 修改密码
      /2fa
        POST:/enable 启用 TOTP
        POST:/disable 禁用 TOTP
        POST:/verify 验证 TOTP
        POST:/reset 重置 TOTP
    /pending
      GET:/list 列出待审核用户
      POST:/approve/{user_id} 批准用户
      POST:/reject/{user_id} 拒绝用户
  /account
    : 复用 Management API 的 /account 接口，但具备所有权限
    : 允许 ?role={user_id} 以某个用户身份操作
  /settings
    GET:/ 获取系统设置
    POST:/ 修改系统设置
  /bulk
    POST:/ 批量操作