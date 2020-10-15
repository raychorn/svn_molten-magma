module Admin::SettingsHelper
  def edit_field
    case @setting.field_type
      when 'text_field'
        text_field('setting','value')
      when 'select'
        select('setting','value', @setting.possible_values)
    end
  end
end
