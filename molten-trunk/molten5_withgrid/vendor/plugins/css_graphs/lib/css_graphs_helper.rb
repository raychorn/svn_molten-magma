module CssGraphsHelper
  # Make a horizontal graph that only shows percentages.
  #
  # The label will be set as the title of the bar element.
  #
  #  horizontal_bar_graph ["Stout", 10], ["IPA", 80], ["Pale Ale", 50], ["Milkshake", 30]
  # 
  def horizontal_bar_graph(*data)
    html = <<-"HTML"
      <style>
      /* Basic Bar Graph */
      .graph { 
        position: relative; /* IE is dumb */
        width: 200px; 
        border: 1px solid #E8112D; 
        padding: 2px; 
        margin-bottom: .5em;					
      }
      .graph .bar { 
        display: block;	
        position: relative;
        background: #E8112D; 
        text-align: center; 
        color: #333; 
        height: 2em; 
        line-height: 2em;									
      }
      .graph .bar span { position: absolute; left: 1em; } /* This extra markup is necessary because IE does not want to follow the rules for overflow: visible */	 
      </style>
    HTML
    
    data.each do |d|
      html += <<-"HTML"
        <div class="graph">
          <strong class="bar" style="width: #{d[1]}%;" title="#{d[0].to_s.humanize}"><span>#{d[1]}%</span> </strong>
        </div>
      HTML
    end
    return html
  end
end
