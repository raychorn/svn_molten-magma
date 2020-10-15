module CssGraphsHelper
  
  # Makes a vertical bar graph.
  #
  #  bar_graph ["Stout", 10], ["IPA", 80], ["Pale Ale", 50], ["Milkshake", 30]
  #
  def bar_graph(*data)
    width = 500
    height = 150
    colors = %w(#ce494a #efba29 #efe708 #5a7dd6 #73a25a)
    floor_cutoff = 24
    
    html = <<-"HTML"
    <style>
      #vertgraph {    				
          width: #{width}px; 
          height: #{height}px; 
          position: relative; 
          font-family: "Lucida Grande", Verdana, Arial;
      }
    
      #vertgraph dl dd {
        position: absolute;
        width: 28px;
        height: 103px;
        bottom: 34px;
        padding: 0 !important;
        margin: 0 !important;
        background-image: url('/images/css_graphs/colorbar.jpg') no-repeat !important;
        text-align: center;
        font-weight: bold;
        color: white;
        line-height: 1.5em;
      }

      #vertgraph dl dt {
        position: absolute;
        width: 48px;
        height: 25px;
        bottom: 0px;
        padding: 0 !important;
        margin: 0 !important;
        text-align: center;
        color: #444444;
        font-size: 0.8em;
      }
    HTML

    bar_offset = 24
    bar_increment = 75
    bar_image_offset = 28
    
    data.each_with_index do |d, index|
      bar_left = bar_offset + (bar_increment * index)
      label_left = bar_left - 10
      background_offset = bar_image_offset * index
      
      html += <<-HTML
        #vertgraph dl dd.#{d[0].to_s.downcase} { left: #{bar_left}px; background-color: #{colors[index]}; background-position: -#{background_offset}px bottom !important; }
        #vertgraph dl dt.#{d[0].to_s.downcase} { left: #{label_left}px; background-position: -#{background_offset}px bottom !important; }
      HTML
    end
    
    html += <<-"HTML"
      </style>
      <div id="vertgraph">
        <dl>
    HTML
    
    data.each_with_index do |d, index|
      html += <<-"HTML"
        <dt class="#{d[0].to_s.downcase}">#{d[0].to_s.humanize}</dt>
        <dd class="#{d[0].to_s.downcase}" style="height: #{d[1]}px;" title="#{d[1]}">#{d[1] < floor_cutoff ? '' : d[1]}</dt>
      HTML
    end
        
    html += <<-"HTML"
        </dl>
      </div>
    HTML
    
    html
  end
  
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
        #border: 1px solid #B1D632; 
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
      .graph .bar span { position: relative; left: 10em; } /* This extra markup is necessary because IE does not want to follow the rules for overflow: visible */	 
      </style>
    HTML
    
    data.each do |d|
      html += <<-"HTML"
        <div class="graph">#{d[0]}
<strong class="bar" style="width: #{d[1]}%;" title="#{d[0].to_s.humanize}"><span>#{d[1]}%</span> </strong>
        </div>
      HTML
    end
    return html
  end
  
  # Makes a multi-colored bar graph with a bar down the middle, representing the value.
  #
  #  complex_bar_graph ["Stout", 10], ["IPA", 80], ["Pale Ale", 50], ["Milkshake", 30]
  #  
  def complex_bar_graph(*data)
    html = <<-"HTML"
      <style>
      /* Complex Bar Graph */
      div#complex_bar_graph dl { 
      	margin: 0; 
      	padding: 0;   
      	font-family: "Lucida Grande", Verdana, Arial;	
      }
      div#complex_bar_graph dt { 
      	position: relative; /* IE is dumb */
      	clear: both;
      	display: block; 
      	float: left; 
      	width: 104px; 
      	height: 20px; 
      	line-height: 20px;
      	margin-right: 17px;              
      	font-size: .75em; 
      	text-align: right; 
      }
      div#complex_bar_graph dd { 
      	position: relative; /* IE is dumb */
      	display: block;   
      	float: left;	 
      	width: 197px; 
      	height: 20px; 
      	margin: 0 0 15px; 
      	background: url("/images/css_graphs/g_colorbar.jpg"); 
      }
      * html div#complex_bar_graph dd { float: none; } /* IE is dumb; Quick IE hack, apply favorite filter methods for wider browser compatibility */
  
      div#complex_bar_graph dd div { 
      	position: relative; 
      	background: url("/images/css_graphs/g_colorbar2.jpg"); 
      	height: 20px; 
      	width: 75%; 
      	text-align:right; 
      }
      div#complex_bar_graph dd div strong { 
      	position: absolute; 
      	right: -5px; 
      	top: -2px; 
      	display: block; 
      	background: url("/images/css_graphs/g_marker.gif"); 
      	height: 24px; 
      	width: 9px; 
      	text-align: left;
      	text-indent: -9999px; 
      	overflow: hidden;
      }
      </style>
      <div id="complex_bar_graph">  
      <dl>
    HTML

    data.each do |d|
      html += <<-"HTML"
        <dt class="#{d[0].to_s.downcase}">#{d[0].to_s.humanize}</dt>
        <dd class="#{d[0].to_s.downcase}" title="#{d[1]}">
        <div style="width: #{d[1]}%;"><strong>#{d[1]}%</strong></div>
      </dd>
    HTML
    end
    
    html += "</dl>\n</div>"
    return html    
  end
end


module SolutionsHelper
  
  # If the specified term is found in the text, then a selection of that text is returned around
  # that term.
  # Otherwise, just the first AppConstants::SOLUTION_SEARCH_NOTE_LIMIT characters are returned.
  def find_and_highlight(text,term)
    return unless text
    begin
    if term and position = text.downcase =~ /#{term.downcase}/
       highlighted = highlight(text.slice( ((start = position - AppConstants::SOLUTION_SEARCH_NOTE_LIMIT/2) < 0 ? 0 : start )..(position + AppConstants::SOLUTION_SEARCH_NOTE_LIMIT/2) ), 
                 term)
       '...' + highlighted + '...'
    else
      truncate(text, AppConstants::SOLUTION_SEARCH_NOTE_LIMIT)
    end
    rescue  RegexpError 
      truncate(text, AppConstants::SOLUTION_SEARCH_NOTE_LIMIT)
    end
  end
  
  # Outputs the link category tree for the given category. 
  # Example: Answers > Contstrants
  def category_links(category)
    links = ""
    iterated_cat = category
    if iterated_cat.parent.nil?
      links = insert_category_link(links,iterated_cat)
    else     
      i = 0
      while !iterated_cat.parent.nil? and iterated_cat != Sfcatnode.root
        links = insert_category_link(links,iterated_cat)
        iterated_cat = iterated_cat.parent
        i+= 1
      end
    end
    links.insert(0,"#{link_to('All Solutions', :action => 'index')}")
  end
  
  def current_category?(category)
    category == @category
  end
  
  def select_tag_for_solution_search_categories(category)
    # set to the root category if it is nil
    category = category || Sfcatnode.root
    parent = category == Sfcatnode.root ? category : category.parent
    select_tag('category_id', options_for_select(categories_for_solution_search(parent).map { |c| [c.name,c.id]  }, category.id))
  end
  
  private
  
  # Generates an array of Catnodes for the solution search limit box. 
  def categories_for_solution_search(category)
    [Sfcatnode.root] + category.children
  end
  
  def insert_category_link(links,category)
    links.insert(0," > #{link_to(category.name, :action => 'category', :id => category)}")
  end
  
  def insert_category(links,category)
    links.insert(0, " > #{category.name}")
  end
end
