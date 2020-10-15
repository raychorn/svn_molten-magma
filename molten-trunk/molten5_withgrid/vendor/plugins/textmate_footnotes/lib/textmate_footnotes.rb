class String
  def line_from_index(index)
    lines = self.to_a
    running_length = 0
    lines.each_with_index do |line, i|
      running_length += line.length
      if running_length > index
        return i
      end
    end
  end
end

class FootnoteFilter
  cattr_accessor :no_style
  self.no_style = false
  
  def self.filter(controller)
    return if controller.render_without_footnotes
    begin
      abs_root = File.expand_path(RAILS_ROOT)
    
      # Some controller classes come with the Controller:: module and some don't (anyone know why? -- Duane)
      controller_filename = "#{abs_root}/app/controllers/#{controller.class.to_s.underscore}.rb".sub('/controllers/controllers/', '/controllers/')
      controller_text = IO.read(controller_filename)
      index_of_method = (controller_text =~ /def\s+#{controller.action_name}[\s\(]/)
      controller_line_number = controller_text.line_from_index(index_of_method) if index_of_method
    
      if controller.instance_variable_get("@performed_render")
        template = controller.instance_variable_get("@template")
        template_path = template.first_render
        template_extension = template.pick_template_extension(template_path).to_s
        template_file_name = template.send(:full_template_path, template_path, template_extension)
        # Need the absolute path for the txmt:// urls
        template_file_name = File.expand_path(template_file_name)

        if ["rhtml", "rxhtml"].include? template_extension
          textmate_prefix = "txmt://open?url=file://"
          controller_url = controller_filename
          controller_url += "&line=#{controller_line_number + 1}" if index_of_method
          
          # If the user would like to be responsible for the styles, let them opt out of the styling here
          unless FootnoteFilter.no_style
            controller.response.body += <<-HTML
            <style>
              #debug {color: #ccc; margin: 40px 5px 5px 5px;}
              #debug a {text-decoration: none; color: #bbb;}
              fieldset.debug_info {text-align: left; border: 1px dashed #aaa; padding: 1em; margin: 1em 2em 1em 2em; color: #777;}
            </style>
            HTML
          end
          
          begin
            controller.response.body += <<-HTML
            <div id="debug">
              <a href="#{textmate_prefix}#{controller_url}">Edit Controller File</a> |
              <a href="#{textmate_prefix}#{template_file_name}">Edit View File</a> |
              <a href="#" onclick="Element.toggle('session_debug_info');return false">Show Session &#10162;</a> |
              <a href="#" onclick="Element.toggle('params_debug_info');return false">Show Params &#10162;</a>
              <fieldset id="session_debug_info" class="debug_info" style="display: none">
                <legend>Session</legend>
                #{debug controller.session}
              </fieldset>
              <fieldset id="params_debug_info" class="debug_info" style="display: none">
                <legend>Params</legend>
                #{debug controller.params}
              </fieldset>
            </div>
            HTML
          rescue Exception => e
            controller.response.body += escape(e.to_s)
          end
        end
      end
    rescue
      # Discard footnotes if there are any problems
    end
  end
  
  def self.debug(object)
    begin
      Marshal::dump(object)
      "<pre class='debug_dump'>#{escape(object.to_yaml).gsub("  ", "&nbsp; ")}</pre>"
    rescue Object => e
      # Object couldn't be dumped, perhaps because of singleton methods -- this is the fallback
      "<code class='debug_dump'>#{escape(object.inspect)}</code>"
    end
  end
  
  def self.escape(text)
    text.gsub("<", "&lt;").gsub(">", "&gt;")
  end
end

class ActionController::Base
  attr_accessor :render_without_footnotes
  
  after_filter FootnoteFilter
  
protected
  alias footnotes_original_render render
  def render(options = nil, deprecated_status = nil, &block) #:doc:
    if options.is_a? Hash
      @render_without_footnotes = (options.delete(:footnotes) == false)
    end
    footnotes_original_render(options, deprecated_status, &block)
  end
end