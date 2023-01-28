from numpy import array, unique
from .dot_values import DotValues
from .axis_values import AxisValues
from .axes_info import AxesInfo
from statistics import mean
class DotData:
    DataVersion = 1.0

    def __init__(self, data_series):
        self.data_series = data_series

        # Note: all coordinate values are relative to the axes origin
        self.dot_values = [DotValues() for series in self.data_series]

    def total_series(self):
        return len(self.dot_values)

    def add_data_series(self, text_label=None, default_points=None):
        # add to data series ...
        self.data_series.append(text_label)

        # prepare doted values
        new_values = DotValues()
        if default_points is not None:
            new_values.points = default_points

        # add to sets of values ....
        self.dot_values.append(new_values)

    def remove_data_series(self, index):
        if 0 <= index <= len(self.data_series):
            # remove from set of doted values ...
            del self.dot_values[index]

            # remove from data series ...
            del self.data_series[index]

            return True
        else:
            return False

    def parse_data(self, chart_info):
        # now infer data quantities based on dot data ...
        # this is very similar to line charts ....
        x1, y1, x2, y2 = chart_info.axes.bounding_box
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # <Start: Identical to Line Charts .. Refactor???>
        if chart_info.axes.x1_axis is not None and chart_info.axes.x2_axis is not None:
            raise Exception("There are two Horizontal Axes, cannot determine the independent variable")

        if chart_info.axes.x1_axis is None and chart_info.axes.x2_axis is None:
            raise Exception("There is no Horizontal Axis!")

        if chart_info.axes.x1_axis is None and chart_info.axes.x2_axis is not None:
            # use upper axis as independent variable axis (very rare)
            x_axis = chart_info.axes.x2_axis
        else:
            # use lower axis as independent variable axis (common)
            x_axis = chart_info.axes.x1_axis

        """
        if ((x_axis.values_type == AxisValues.ValueTypeNumerical and x_axis.scale_type == AxisValues.ScaleNone) or
            (x_axis.values_type == AxisValues.ValueTypeCategorical)):
            # only sample at known points (label values on the axis)
            axis_ticks = x_axis.ticks_with_labels()

            var_x_pixel_points = []
            var_x_chart_values = []
            for tick_info in axis_ticks:
                tick_label = chart_info.axes.tick_labels[tick_info.label_id]

                if x_axis.ticks_type == AxisValues.TicksTypeMarkers:
                    # for marker ticks .. use position as annotated ..
                    var_x_pixel_points.append(tick_info.position)
                else:
                    # for separator ticks ... use center of label ...
                    pos_x, pos_y = tick_label.get_center()
                    var_x_pixel_points.append(pos_x)

                var_x_chart_values.append(tick_label.value)
        else:
            # sample based on line data ....
            var_x_pixel_points = None
            var_x_chart_values = None
        """
        # <End: Identical to Line Charts .... Refactor??>

        # for each data series ...
        data_series = []
        all_dot_points = []
        for series_idx, series_text in enumerate(self.data_series):
            # data series = list of lists of (X, Y) coordinates in logical coordinates (chart-space)
            # all_dot_points = List of lists of (X, Y) coordinates in image coordinates (pixel-space)
            dot = self.dot_values[series_idx]

            current_data_series = []
            current_dot_points = []

            # For each point in the dot
            for p_idx, (p_x, p_y) in enumerate(dot.points):
                # first convert the X coordinate to a value ...
                # assume (p_x, p_y) are coordinates relative to the data series)
                # convert to pixel space
                line_x_pixel = p_x + x1
                line_y_pixel = y2 - p_y

                line_data_point = {
                    "x": line_x_pixel,
                    "y": line_y_pixel,
                }
                current_dot_points.append(line_data_point)

                if x_axis.values_type == AxisValues.ValueTypeNumerical or x_axis.values_type == AxisValues.ValueTypeNumericalInt:
                    proj_x_val = AxisValues.Project(chart_info.axes, x_axis, False, line_x_pixel)
                    # print("-------------------------")
                    # print("PROJECTED X VALUE:")
                    # print(proj_x_val)
                    # print("-------------------------")
                else:
                    # categorical x axis ... find closest category
                    proj_x_val = AxisValues.FindClosestValue(chart_info.axes, x_axis, False, line_x_pixel)

                data_series_point = {
                    "x": proj_x_val,
                }
                # get Y value on chart space ...
                # Y-1 axis (Common)
                if chart_info.axes.y1_axis is not None:
                    if chart_info.axes.y1_axis.values_type == AxisValues.ValueTypeNumerical or chart_info.axes.y1_axis.values_type == AxisValues.ValueTypeNumericalInt:
                        proj_y_val = AxisValues.Project(chart_info.axes, chart_info.axes.y1_axis, True, line_y_pixel)
                    else:
                        # categorical x axis ... find closest category
                        proj_y_val = AxisValues.FindClosestValue(chart_info.axes, chart_info.axes.y1_axis, True, line_y_pixel)
                    data_series_point["y"] = proj_y_val

                current_data_series.append(data_series_point)
        
            if series_text is None:
                series_name = "[unnamed data series #{0:d}]".format(series_idx)
            else:
                series_name = series_text.value
            # if there's a single-axis vertical dot graph, collate the points.
            # this behaves differently based on numerical / categorical axes because we need to catch in-between values 
            if chart_info.axes.x1_axis and chart_info.axes.y1_axis is None:
                if chart_info.axes.x1_axis.values_type == AxisValues.ValueTypeNumerical or chart_info.axes.x1_axis.values_type == AxisValues.ValueTypeNumericalInt:
                    collated_data_series = []
                    # plural data series: all of the points in the chart (not unique)
                    plural_data_series = sorted([list(each.values())[0] for each in current_data_series])
                    # xvalues: list representation of all entries on x axis
                    # to find these, we need a margin by which we can group these together. for now, 1/10th of the pixels in a tick converted to value 
                    tickvalues = sorted([float(each.value) for each in chart_info.axes.get_axis_labels(AxesInfo.AxisX1)])
                    ticks = [each.position for each in chart_info.axes.x1_axis.ticks]
                    sorted_tick_positions = sorted(ticks)
                    value_per_tick = abs(tickvalues[0] - tickvalues[1])
                    pixels_per_tick = sorted_tick_positions[1] - sorted_tick_positions[0]
                    value_per_pixel = value_per_tick / pixels_per_tick
                    # we want 1/20 of the pixel per tick converted to value 
                    margin = (pixels_per_tick / 20 ) * value_per_pixel
                    # print("***")
                    # print("pixels in a whole tick: ", pixels_per_tick) 
                    # print("value in a whole tick:", value_per_tick)
                    # print("margin value: ", margin)
                    # print("***")
                    # to get the interpolated data series, add 1 to a bucket for each point in the sorted plural data series-
                    # making a new bucket every time the distance between the most recent two values is greater than our margin.

                    points = []
                    points.append([plural_data_series[0]])
                    active_point_index = 0
                    for i in range(1, len(plural_data_series)):
                        # when we've found a point within the margin of the avg for our bucket 
                        if abs(abs(plural_data_series[i]) - abs(mean(points[active_point_index]))) <= margin:
                            # print(abs(abs(plural_data_series[i]) - abs(mean(points[active_point_index]))), "was less than ", margin) 
                            points[active_point_index].append(plural_data_series[i])
                        # when we've found a point outside the margin, make a new entry
                        else:
                            points.append([plural_data_series[i]])
                            active_point_index += 1

                    
                    
                    for each in points:
                        collated_data_series.append({mean(each) : len(each)})

                else:
                    collated_data_series = [] 
                    # plural data series: all of the points in the chart (not unique)
                    plural_data_series = [list(each.values())[0] for each in current_data_series] 
                    # tickvalues: list representation of the tick values on x axis
                    tickvalues = [each.value for each in chart_info.axes.get_axis_labels(AxesInfo.AxisX1)]
                    # values / counts: values and frequency of values in the chart
                    values, counts = unique(array(plural_data_series), return_counts=True)
                    counts = [int(item) for item in counts]
                    for each in tickvalues:
                        if each in values:
                            collated_data_series.append({each : counts[list(values).index(each)]})
                        else:
                            collated_data_series.append({each : 0})
                
                current_data_series = collated_data_series

            final_data_series = {
                "data": current_data_series,
                "name": series_name,
            }

            data_series.append(final_data_series)
            all_dot_points.append(current_dot_points)

        return all_dot_points, data_series

    @staticmethod
    def Copy(other):
        assert isinstance(other, DotData)

        # copy object ....
        data = DotData(list(other.data_series))

        # create copy of the individual lines ...
        for idx, dot_values in enumerate(other.dot_values):
            data.dot_values[idx] = DotValues.Copy(dot_values)

        return data

    @staticmethod
    def CreateDefault(chart_info):
        # first, determine data series ...
        data_series = chart_info.get_data_series_candidates()

        data = DotData(data_series)

        # There is no such thing as a good default set of points for dot plots ....
        # ... only if these were taken from image analysis ...

        return data

    def to_XML(self, indent=""):
        xml_str = indent + '<Data class="DotData">\n'
        # data series ...
        xml_str += indent + "    <DataSeries>\n"
        for series in self.data_series:
            if series is None:
                xml_str += indent + "        <TextId></TextId>\n"
            else:
                xml_str += indent + "        <TextId>{0:d}</TextId>\n".format(series.id)
        xml_str += indent + "    </DataSeries>\n"

        # data values ...
        xml_str += indent + "    <ChartValues>\n"
        for dot_values in self.dot_values:
            xml_str += dot_values.to_XML(indent + "        ")
        xml_str += indent + "    </ChartValues>\n"
        xml_str += indent + '</Data>\n'

        return xml_str

    @staticmethod
    def FromXML(xml_root, text_index):
        # assume xml_root is Data
        data_series = []
        for xml_text_id in xml_root.find("DataSeries").findall("TextId"):
            text_id = xml_text_id.text
            if text_id is None or text_id.strip() == "":
                # an empty data series
                data_series.append(None)
            else:
                data_series.append(text_index[int(text_id)])

        data = DotData(data_series)
        for idx, xml_dot_values in enumerate(xml_root.find("ChartValues").findall("DotValues")):
            data.dot_values[idx] = DotValues.FromXML(xml_dot_values)

        return data

