module HomeHelper
  # Creates a link to sort the results by the specified column.
  def link_to_sort(name,column)
    if column == @sort
      order = ('ASC' == @order ? 'DESC' : 'ASC')
    else
      order = 'ASC'
    end
    link = link_to(name, params.merge({:sort => column, :order => order}))
    image = build_sort_image(column,order)
    "#{link} #{image}"
  end
  
  # Creates a sort arrow indictator. If +@sort+ isn't set, we default to display next to 
  # 'uploaded'
  def build_sort_image(column,order)
    if column == @sort or (@sort.nil? and column == 'uploaded')
      image_tag("icons/#{order}.gif", :width => 7, :height => 5, :alt => order)
    end
  end
end
