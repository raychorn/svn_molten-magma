module CasesHelper
  def link_to_toggle_additional_information(name = "Additional Information")
    link_to_function name, "Element.toggle('case_additional_information');
                            Element.toggle('show_info');
                            Element.toggle('hide_info');",
                            :id => 'toggle_additional_info'
  end
  
  def search?
    controller.action_name == 'search'
  end
  
  def tag_for_cases(status)
    "#{status}_cases"
  end
  
  def tag_for_hide_cases(status)
    "hide_#{status}"
  end
  
  def tag_for_show_cases(status)
    "show_#{status}"
  end
  
  def grid_header_for(cols)
    _cols_ = '"Case #","Status","Subject"'
    cols.each do |col|
      if _cols_.length > 0
        _cols_ += ','
      end
      _cols_ += '"' + col[:desc] + '"'
    end
    _cols_
  end

  def grid_data_for(cols,cases)
    _id_ = 1
    data = '<?xml version="1.0" encoding="UTF-8"?>'
    data += "<rows>"
    cases.each do |aCase|
      data += '<row id="' + _id_.to_s + '">'
      data += "<cell>" + aCase.stripped_case_number + "</cell>"
      data += "<cell>" + aCase.status + "</cell>"
      data += "<cell>" + aCase.subject + "</cell>"
      cols.each do |col|
        begin
          val = eval "aCase.#{col[:meth]}"
          val = val.split(10.chr)
          val = val.join(' ')
          data += "<cell>" + val.to_s + "</cell>"
        rescue
        end
      end
      data += '</row>'
      _id_ += 1
    end
    data += "</rows>"
    data
  end

  def grid_params_for(cases)
    data = []
    cases.each do |aCase|
      data.push(aCase.stripped_case_number + "=1")
    end
    data.join('&')
  end

  def grid_widths_for(cols,max_width)
    w = max_width / (cols.length + 3)
    _cols_ = w.to_s + "," + w.to_s + "," + w.to_s
    cols.each do |col|
      if _cols_.length > 0
        _cols_ += ','
      end
      _cols_ += w.to_s
    end
    '"' + _cols_ + '"'
  end

  def grid_aligns_for(cols)
    _cols_ = "left,left,left"
    cols.each do |col|
      if _cols_.length > 0
        _cols_ += ','
      end
      _cols_ += "left"
    end
    '"' + _cols_ + '"'
  end

  def rowspan_size
    (params[:all] ? current_contact.settings.case_columns_setting.all_selected_case_columns.size+2 : current_contact.settings.case_columns_setting.your_selected_case_columns.size+2)
  end
  
  # Creates a link to sort the results by the specified column.
  # No links are created when searching.
  def link_to_sort(name,column)
    return name if search?
    if column == @sort
      order = ('ASC' == @order ? 'DESC' : 'ASC')
    else
      order = 'ASC'
    end
    if column == 'account'
      column = 'sfcase.account_id'
    end
    link = link_to(name, params.merge({:sort => column, :order => order}))
    image = build_sort_image(column,order)
    "#{link} #{image}"
  end
  
  # Sends to +list_beta+ if no case report. Otherwise, sends to 
  # +case_report+. 
  def url_for_filters
    if @case_report
      url_for({:action => 'report', :id => @case_report})
    else
      url_for({:action => 'list_beta'})
    end
  end
  
  # True if the account filter logic should be available. 
  def account_filter_viewable?
    current_contact.privilege?(AppConstants::PRIVILEGE[:user_manager]) and current_contact.company.children.size > 0
  end
  
  # Generates an Array of case statuses that should be saved with created case reports. 
  # The array of statuses reflects the statuses used in the current view. 
  #
  # - Not viewing a report => Status array from current contact
  # - Viewing a report w/params[:status] empty => Status array from current report
  # - Viewing a report w/params[:status] NOT empty => Status array from params[:status]
  def case_report_status_array
    if @case_report_status_array
      @case_report_status_array
    elsif @case_report.nil?
      @case_report_status_array = current_contact.set_case_filters
    elsif @case_report.status_array
      if params[:status].is_a?(Array)
        @case_report_status_array = params[:status]
      else
        @case_report_status_array = @case_report.status_array
      end
    else
      @case_report_status_array = current_contact.set_case_filters
    end
  end
  
  # Generates an Array of accounts that should be saved with created case reports. 
  # The array of accounts reflects the accounts used in the current view. 
  #
  # - Not viewing a report => Account array from current contact
  # - Viewing a report w/params[:accounts] empty => Account array from current report
  # - Viewing a report w/params[:accounts] NOT empty => Account array from params[:accounts]
  def case_report_account_array
    if @case_report_account_array
      @case_report_account_array
    elsif @case_report.nil?
      @case_report_account_array = current_contact.set_account_filters
    elsif @case_report.account_array
      if params[:accounts].is_a?(Array)
        @case_report_account_array = Sfaccount.find(params[:accounts])
      else
        @case_report_account_array = @case_report.account_array
      end
    else
      @case_report_account_array = current_contact.set_account_filters
    end
  end
  
  def case_report_column_array
    @case_report_column_array ||= if @case_report.nil?
                                    contact_case_cols.map { |c| c[:attr] }
                                  elsif @case_report.column_array
                                    if params[:columns].is_a?(Array)
                                      params[:columns]
                                    else
                                      @case_report.column_array
                                    end
                                  else
                                    contact_case_cols.map { |c| c[:attr] }
                                  end
  end
  
  # Creates a button and link to subscribe or unsubscribe to the
  # +current_user+'s account cases.
  def link_to_subscribe_to_cases
   html = if current_contact.share_cases?(current_contact.company)
            link_to image_tag('buttons/share_cases.gif'),
                    :controller => 'case_watchers',
                    :action => 'account',
                    :id => current_contact.company   
     elsif SfcaseWatcher.find_for_contact_and_account(current_contact)
            link_to_remote image_tag('buttons/unsubscribe.gif'), 
                     {:url => {:controller => 'case_watchers',
                              :action => 'unsubscribe',
                              :account => current_contact.company.id,
                              :from => controller.action_name},
                      :loading => "Element.toggle('sub_indicator');Element.hide('subscribe_link')"
                     },
                     {:id => 'subscribe_link'}
   else
      link_to_remote image_tag('buttons/subscribe.gif'), 
                     {:url => {:controller => 'case_watchers',
                              :action => 'subscribe',
                              :account => current_contact.company.id,
                              :from => controller.action_name},
                      :loading => "Element.toggle('sub_indicator');Element.hide('subscribe_link')"
                     },
                     {:id => 'subscribe_link'}
    end
    html += sub_indicator
    html
  rescue  ActiveRecord::StatementInvalid
    "connection error"
  end
  
  def link_to_subscribe_to_case(support_case = @case, options = {})
    html = if current_contact.share_cases?(current_contact.company)
              link_to image_tag('buttons/share_this_case.gif'),
                      :controller => 'case_watchers',
                      :action => 'case',
                      :id => support_case
          elsif !options[:subscribe] and SfcaseWatcher.find_for_contact_and_support_case(current_contact, support_case)
              link_to_remote image_tag('buttons/unsubscribe.gif'), 
                             {:url => {:controller => 'case_watchers',
                                      :action => 'unsubscribe',
                                      :support_case => support_case.id, 
                                      :from => controller.action_name},
                              :loading => "Element.toggle('sub_indicator');Element.hide('subscribe_link')"
                             },
                             {:id => 'subscribe_link'}
          else
            link_to_remote image_tag('buttons/subscribe.gif'), 
                           {:url => {:controller => 'case_watchers',
                                    :action => 'subscribe',
                                    :support_case => support_case.id,
                                    :from => controller.action_name},
                            :loading => "Element.toggle('sub_indicator');Element.hide('subscribe_link')"
                           },
                           {:id => 'subscribe_link'}
         end
    html += sub_indicator
    html
  rescue
  end
  
  def set_subscribe_link(options = {})
    if params[:from] == 'show'
      link_to_subscribe_to_case(Sfcase.find(params[:support_case]), options)
    else
      link_to_subscribe_to_cases
    end
  end
  
  ### Form Helpers ###
  # These are used to only make the field editable if:
  # - the associated +@case+ is new
  # - the case is an existing case and the attribute is listed in Sfcase::EDITABLE_ATTRIBUTES
  
  
  # def case_text_field(object_name, method, options = {})
  #     sfcase = instance_variable_get(object_name)
  #     if sfcase.new_record? or Sfcase::EDITABLE_ATTRIBUTES.include?(method.to_s)
  #       text_field(object_name, method, options = {})
  #     else
  #       sfcase.send(method)
  #     end
  #   end
  
  def case_text_field(object_name, method, options = {})
    sfcase = instance_variable_get('@'+object_name)
    do_case_form_field(sfcase, method) { text_field(object_name, method, options) }
  end
  
  def case_select_tag(name, option_tags = nil, options = {})
    sfcase = @case
    name =~ /\[\w+\]/ 
    method = $&.gsub(/\[|\]/,'')
    do_case_form_field(sfcase, method) { select_tag(name, option_tags, options) }
  end
  
  def case_text_area(object_name, method, options = {})
    sfcase = instance_variable_get('@'+object_name)
    do_case_form_field(sfcase, method) { text_area(object_name, method, options) }
  end
  
  def case_date_select(object_name, method, options = {})
    sfcase = instance_variable_get('@'+object_name)
    do_case_form_field(sfcase, method) { date_select(object_name, method, options) }
  end
  
  def do_case_form_field(sfcase, method)
    if sfcase.new_record? or Sfcase::EDITABLE_ATTRIBUTES.include?(method.to_s)
      yield
    else
      html = "<span style='font-weight:normal; width: 100%;'>"
      html << (sfcase.send(method).to_s || 'N/A')
      html << '</span>'
    end
  end
  
  private
  
  def sub_indicator
    html =<<-END_STRING
      <div style="display:none" id='sub_indicator'>
				#{image_tag('indicator_arrows_circle.gif', 
					:style => "margin-left:42px;margin-right:42px;padding-top:5px")}
			</div>
    END_STRING
  end
  
  # Creates a sort arrow indictator. If +@sort+ isn't set, we default to display next to 
  # 'last updated'
  def build_sort_image(column,order)
    if column == @sort or (@sort.nil? and column == 'sfcase.last_modified_date')
      image_tag("icons/#{order}.gif", :width => 7, :height => 5, :alt => order)
    end
  end
end
