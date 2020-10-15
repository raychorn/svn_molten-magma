class AddShutdownAppSetting < ActiveRecord::Migration
  def self.up
    AppSetting.create!(:name => "SHUTDOWN_DATES",
                      :value => "2",
                      :field_type => 'text_field')

    AppSetting.create!(:name => "SHUTDOWN_DATE_RANGE1",
                      :value => "06/28/2008,07/06/2008",
                      :field_type => 'text_field')

    AppSetting.create!(:name => "SHUTDOWN_MESSAGE1",
                      :value => "AppConstants::SHUTDOWN_NOTICE",
                      :field_type => 'text_field')

    AppSetting.create!(:name => "SHUTDOWN_DATE_RANGE2",
                      :value => "07/19/2008,07/20/2008",
                      :field_type => 'text_field')

    AppSetting.create!(:name => "SHUTDOWN_MESSAGE2",
                      :value => "Dear Customer,<br><br>SalesForce is observing a slowdown today due to regular system maintenance that may result in some delays ot slow connections.<br><br>Thank you for your co-operation and understanding.<br><br>Sincerely,<br>MOLTEN TEAM USA",
                      :field_type => 'text_field')
  end

  def self.down
    AppSetting.find_by_name("SHUTDOWN_DATES").destroy
    AppSetting.find_by_name("SHUTDOWN_DATE_RANGE1").destroy
    AppSetting.find_by_name("SHUTDOWN_MESSAGE1").destroy
    AppSetting.find_by_name("SHUTDOWN_DATE_RANGE2").destroy
    AppSetting.find_by_name("SHUTDOWN_MESSAGE2").destroy
  rescue
  end
end
