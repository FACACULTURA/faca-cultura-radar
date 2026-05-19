import React, { useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  StyleSheet,
  View,
} from "react-native";
import FcultVeil from "./FcultVeil";

const { width } = Dimensions.get("window");

const CARD_WIDTH = width * 0.78;
const CARD_GAP = 18;
const SNAP = CARD_WIDTH + CARD_GAP;

type Props<T> = {
  data: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T, index: number) => string;
};

export default function FcultCarousel<T>({
  data,
  renderItem,
  keyExtractor,
}: Props<T>) {
  const scrollX = useRef(new Animated.Value(0)).current;
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <View>
      <View style={styles.carouselArea}>
        <Animated.FlatList
          data={data}
          horizontal
          showsHorizontalScrollIndicator={false}
          snapToInterval={SNAP}
          decelerationRate="normal"
          bounces
          keyExtractor={keyExtractor}
          contentContainerStyle={styles.carouselContent}
          onMomentumScrollEnd={(event) => {
            const index = Math.round(event.nativeEvent.contentOffset.x / SNAP);
            setActiveIndex(index);
          }}
          onScroll={Animated.event(
            [{ nativeEvent: { contentOffset: { x: scrollX } } }],
            { useNativeDriver: true }
          )}
          renderItem={({ item, index }) => {
            const inputRange = [
              (index - 1) * SNAP,
              index * SNAP,
              (index + 1) * SNAP,
            ];

            const scale = scrollX.interpolate({
              inputRange,
              outputRange: [0.72, 1, 0.72],
              extrapolate: "clamp",
            });

            const opacity = scrollX.interpolate({
              inputRange,
              outputRange: [0.34, 1, 0.34],
              extrapolate: "clamp",
            });

            const translateY = scrollX.interpolate({
              inputRange,
              outputRange: [28, 0, 28],
              extrapolate: "clamp",
            });

            return (
              <Animated.View
                style={[
                  styles.cardWrap,
                  {
                    opacity,
                    transform: [{ scale }, { translateY }],
                  },
                ]}
              >
                {renderItem(item, index)}
              </Animated.View>
            );
          }}
        />

        <FcultVeil left right />
      </View>

      <View style={styles.dots}>
        {data.map((item, index) => (
          <View
            key={keyExtractor(item, index)}
            style={[styles.dot, activeIndex === index && styles.dotActive]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  carouselArea: {
    height: 460,
    justifyContent: "center",
  },

  carouselContent: {
    paddingHorizontal: (width - CARD_WIDTH) / 2,
    alignItems: "center",
  },

  cardWrap: {
    width: CARD_WIDTH,
    marginRight: CARD_GAP,
  },

  dots: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 12,
    gap: 7,
  },

  dot: {
    width: 7,
    height: 7,
    borderRadius: 7,
    backgroundColor: "#D6D1E0",
  },

  dotActive: {
    width: 18,
    backgroundColor: "#FF6D00",
  },
});