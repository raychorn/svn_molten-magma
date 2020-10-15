class GridController < ProtectedController

  def list
  end

  def grid_data
  return_data = <<-EOF
<?xml version="1.0" encoding="UTF-8"?>
<rows>
    <row id="a">
        <cell>Model 1</cell>
        <cell>100</cell>
        <cell>399</cell>
    </row>
    <row id="b">
        <cell>Model 2</cell>
        <cell>50</cell>
        <cell>649</cell>
    </row>
    <row id="c">
        <cell>MOdel 3</cell>
        <cell>70</cell>
        <cell>499</cell>
    </row>
</rows>
EOF
    render :xml => return_data
  end

  def data
    ids = params.keys()
  return_data = <<-EOF
<?xml version="1.0" encoding="UTF-8"?>
<rows>
    <row id="a">
        <cell>1</cell>
        <cell>2</cell>
        <cell>3</cell>
        <cell>4</cell>
        <cell>5</cell>
        <cell>6</cell>
        <cell>7</cell>
        <cell>8</cell>
        <cell>9</cell>
        <cell>10</cell>
    </row>
</rows>
EOF
    render :xml => return_data
  end

end
