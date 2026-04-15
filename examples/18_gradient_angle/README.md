# Example 18 - Gradient Angle on Multi-line Text

Demonstrates the `gradient_angle` parameter by rendering the same wrapped
text at five different angles, making it easy to compare the visual effect.

## What it does

Renders five panels of the same rainbow-gradient text wrapped at 500 px,
each with a different `gradient_angle` value:

1. **0 degrees** - pure left-to-right gradient. Every line gets the same
   color band at the same horizontal position.
2. **15 degrees (default)** - slight diagonal tilt. Each successive line
   shifts the color ramp, giving multi-line text natural color variation.
3. **30 degrees** - more pronounced diagonal.
4. **45 degrees** - strong diagonal sweep across the text block.
5. **90 degrees** - pure top-to-bottom gradient. Colors change between
   lines rather than across them.

## Key takeaways

- `gradient_angle` defaults to `15.0` degrees, which works well for most
  multi-line text because each line gets a slightly different slice of the
  color ramp.
- Set `gradient_angle=0.0` for a classic left-to-right gradient where every
  line looks the same horizontally.
- Higher angles (45, 90) create more dramatic line-to-line color shifts,
  which can be useful for short text blocks or headings.
- The angle applies to all gradient parameters: `fill`, `stroke_fill`, and
  `shadow_color`.
