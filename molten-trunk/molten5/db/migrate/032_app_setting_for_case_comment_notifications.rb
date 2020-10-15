class AppSettingForCaseCommentNotifications < ActiveRecord::Migration
  def self.up
    AppSetting.create(:name => "Send Comment Notifications",
                      :value => AppSetting::SEND_COMMENT_NOTIFICATIONS[:do_not_send_notification],
                      :field_type => 'select')
  end

  def self.down
    if setting = AppSetting.find_by_name('Send Comment Notifications')
      setting.destroy
    end
  end
end
