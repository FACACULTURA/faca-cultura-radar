import React from "react";
import { ScrollView, StyleSheet, ViewStyle } from "react-native";

type Props = {
  children: React.ReactNode;
  style?: ViewStyle;
  contentStyle?: ViewStyle;
  horizontal?: boolean;
};

export default function FcultScroll({
  children,
  style,
  contentStyle,
  horizontal = false,
}: Props) {
  return (
    <ScrollView
      horizontal={horizontal}
      showsVerticalScrollIndicator={false}
      showsHorizontalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
      style={[styles.scroll, style]}
      contentContainerStyle={[
        horizontal ? styles.horizontalContent : styles.verticalContent,
        contentStyle,
      ]}
    >
      {children}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
  },

  verticalContent: {
    paddingHorizontal: 30,
    paddingTop: 50,
    paddingBottom: 170,
  },

  horizontalContent: {
    paddingHorizontal: 24,
    paddingVertical: 20,
    alignItems: "center",
  },
});